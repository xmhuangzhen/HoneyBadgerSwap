extern crate rand;
extern crate curve25519_dalek_ng;
use curve25519_dalek_ng::scalar::{Scalar, UnpackedScalar};
use curve25519_dalek_ng::ristretto::CompressedRistretto;
extern crate merlin;
use merlin::Transcript;
extern crate bulletproofs;
use bulletproofs::{BulletproofGens, PedersenGens, RangeProof};
use pyo3::prelude::*;

/// Given `data` with `len >= 32`, return the first 32 bytes.
pub fn read32(data: &[u8]) -> [u8; 32] {
    let mut buf32 = [0u8; 32];
    buf32[..].copy_from_slice(&data[..32]);
    buf32
}

// What will happen if we have more than 2^64 servers? Although it is extremely impossible, can
// adversarry exploit this?
pub fn lagrange_coefficient(covariate_u64: u64, others_u64: Vec<u64>) -> PyResult<Scalar> {
    let covariate = Scalar::from(covariate_u64);
    let others: Vec<_> = others_u64
        .iter()
        .map(|v| Scalar::from(*v))
        .collect();

    let denominator_factors: Vec<_> = others
        .iter()
        .map(|v| covariate - v)
        .collect();
    let numerator_factors: Vec<_> = others
        .iter()
        .map(|v| -v)
        .collect();
    
    let denominator = denominator_factors.iter().copied().reduce(|a, b| a * b).unwrap();
    let numerator = numerator_factors.iter().copied().reduce(|a, b| a * b).unwrap();

    let coefficient = numerator * denominator.invert();
    
    Ok(coefficient)
}

#[pyfunction]
fn pedersen_commit(secret_value_bytes: [u8; 32], blinding_bytes: [u8; 32]) -> PyResult<[u8; 32]> {
    let secret_value = Scalar::from_bytes_mod_order(secret_value_bytes);
    let blinding = Scalar::from_bytes_mod_order(blinding_bytes);

    let pc_gens = PedersenGens::default();
    let commitment = pc_gens.commit(secret_value, blinding);

    Ok(commitment.compress().to_bytes())
}

#[pyfunction]
fn pedersen_open(secret_value: u64, blinding: u64, commitment_bytes: [u8; 32]) -> PyResult<bool> {
    let secret_value_scalar = Scalar::from(secret_value);
    let blinding_scalar = Scalar::from(blinding);
    let pc_gens = PedersenGens::default();
    let opened_commitment_bytes = pc_gens.commit(secret_value_scalar, blinding_scalar).compress().to_bytes();
    Ok(opened_commitment_bytes == commitment_bytes)
}


#[pyfunction]
fn pedersen_aggregate(commitment_bytes_list: Vec<[u8; 32]>, covariates: Vec<u64>) -> PyResult<[u8;32]> {
    let commitment_list: Vec<_> = commitment_bytes_list
        .iter()
        .map(|v| CompressedRistretto(read32(v)).decompress().unwrap())
        .collect();

    let scaled_commitment_list: Vec<_> = commitment_list
        .iter()
        .enumerate()
        .map(|(idx, v)| v * lagrange_coefficient(covariates[idx], [&covariates[..idx], &covariates[idx+1..]].concat()).unwrap())
        .collect();

    let commitment = scaled_commitment_list.iter().copied().reduce(|a, b| a + b).unwrap();
    // TODO: figure out if the list is in the correct order.
    // for commitment_bytes in commitment_bytes_list.iter() {
    //     commitment_list.push(CompressedRistretto(read32(commitment_bytes)).decompress());
    // }

    // TODO: take in a list of Pedersen commitment. Interpolate them.
    // TODO: upgrade to robust version.
    Ok(commitment.compress().to_bytes())
}

#[pyfunction]
fn pedersen_compare(recovered_commitment: [u8; 32], onchain_commitment: [u8; 32]) -> PyResult<bool> {
    Ok(recovered_commitment == onchain_commitment)
}

// TODO: return the blinding as bytes using as_bytes (returns &[u8; 32])
#[pyfunction]
fn zkrp_prove(secret_value: u64, bits: usize) -> PyResult<(Vec<u8>, [u8; 32], [u8; 32])> {
    // Generators for Pedersen commitments.  These can be selected
    // independently of the Bulletproofs generators.
    let pc_gens = PedersenGens::default();

    // Generators for Bulletproofs, valid for proofs up to bitsize 64
    // and aggregation size up to 1.
    let bp_gens = BulletproofGens::new(64, 1);

    // The API takes a blinding factor for the commitment.
    let blinding = Scalar::random(&mut rand::thread_rng());

    // The proof can be chained to an existing transcript.
    // Here we create a transcript with a doctest domain separator.
    let mut prover_transcript = Transcript::new(b"zkrp");

    // Create a 32-bit rangeproof.
    let (proof, committed_value) = RangeProof::prove_single(
        &bp_gens,
        &pc_gens,
        &mut prover_transcript,
        secret_value,
        &blinding,
        bits,
    ).expect("A real program could handle errors");

    Ok((proof.to_bytes(), committed_value.to_bytes(), blinding.to_bytes()))
}

#[pyfunction]
fn zkrp_verify(proof_bytes: Vec<u8>, committed_value_bytes: [u8; 32]) -> PyResult<bool> {
    // Generators for Pedersen commitments.  These can be selected
    // independently of the Bulletproofs generators.
    let pc_gens = PedersenGens::default();

    // Generators for Bulletproofs, valid for proofs up to bitsize 64
    // and aggregation size up to 1.
    let bp_gens = BulletproofGens::new(64, 1);

	let proof = RangeProof::from_bytes(proof_bytes.as_slice()).expect("Error: Proof deserialization failed!");
    let committed_value = CompressedRistretto(read32(&committed_value_bytes));
    // Verification requires a transcript with identical initial state:
    let mut verifier_transcript = Transcript::new(b"zkrp");
    Ok(proof.verify_single(&bp_gens, &pc_gens, &mut verifier_transcript, &committed_value, 32).is_ok())
}

#[pyfunction]
fn gen_random_value(value_num: u64) -> PyResult<Vec<[u8; 32]>> {
    let mut res_val : Vec<[u8; 32]> = Vec::new();

    let mut i = 0;

    while i < value_num {
        let cur_res = Scalar::random(&mut rand::thread_rng());
        res_val.push(cur_res.to_bytes());
        i = i + 1;
    }

    Ok(res_val)
}


#[pyfunction]
fn zkrp_prove_mul(x_v: u64, rx_prime_bytes: [u8; 32], ry_prime_bytes: [u8; 32]) -> PYResult<[u8; 32]> {
    let pc_gens = PedersenGens::default();

    let x = Scalar::from(x_v);
    let rx_prime = Scalar::from_bytes_mod_order(rx_prime_bytes);
    let ry_prime = Scalar::from_bytes_mod_order(ry_prime_bytes);

    let kx = Scalar::random(&mut rand::thread_rng());
    let kx_prime = Scalar::random(&mut rand::thread_rng());
    let ky = Scalar::random(&mut rand::thread_rng());
    let ky_prime = Scalar::random(&mut rand::thread_rng());
    let rz = Scalar::random(&mut rand::thread_rng());
    let kz_prime = Scalar::random(&mut rand::thread_rng());

    let com_kx = pc_gens.commit(kx, kx_prime).compress();
    let com_ky = pc_gens.commit(ky, ky_prime).compress();

    // com_kz = pc_gens.commit(x*ky, -rx_prime*ky + kz_prime);
    let t1_value:Scalar = (x * ky).reduce();
    let t1_blinding_value:Scalar = (kz_prime - (rx_prime * ky).reduce()).reduce();
    let com_kz = pc_gens.commit(t1_value, t1_blinding_value).compress();

    let mut prover_transcript = Transcript::new(b"zkrpmul");
    let c = prover_transcript.challenge_scalar(b"c");
    
    let sx:Scalar = ((c*x).reduce() + kx).reduce(); // sx = c * x + kx
    let sy:Scalar = ((c*y).reduce() + ky).reduce(); // sy = c * y + ky
    let sx_prime:Scalar = (kx_prime - (c*rx_prime).reduce()).reduce(); // sx' = c * (-rx') + kx'
    let sy_prime:Scalar = (ky_prime - (c*ry_prime).reduce()).reduce(); // sy' = c * (-ry') + ky'
    let sz_prime:Scalar = ((c*rz).reduce() + kz_prime).reduce(); // sz' = c * rz + kz'

    

    Ok(c.to_bytes())
}

#[pyfunction ]
fn zkrp_verify_mul(mx_bytes: [u8; 32], my_bytes: [u8; 32], c_rx_bytes: [u8; 32], c_ry_bytes: [u8; 32]) -> PyResult<()> {
    let mx = Scalar::from_bytes_mod_order(mx_bytes);
    let my = Scalar::from_bytes_mod_order(my_bytes);
    let c_rx = Scalar::from_bytes_mod_order(c_rx_bytes);
    let c_ry = Scalar::from_bytes_mod_order(c_ry_bytes);
    let zer = Scalar::zero();

    let pc_gens = PedersenGens::default();

    let g_mx = pc_gens.commit(mx,zer).compress();
    let c_x = (c_rx * (g_mx.invert())).reduce();
    let g_my = pc_gens.commit(my,zer).compress();
    let c_y = (c_ry * (g_my.invert())).reduce();

    Ok(())
}

/// A Python module implemented in Rust.
#[pymodule]
fn zkrp_pyo3(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(pedersen_commit, m)?)?;
    m.add_function(wrap_pyfunction!(pedersen_open, m)?)?;
    m.add_function(wrap_pyfunction!(pedersen_aggregate, m)?)?;
    m.add_function(wrap_pyfunction!(pedersen_compare, m)?)?;
    m.add_function(wrap_pyfunction!(zkrp_prove, m)?)?;
    m.add_function(wrap_pyfunction!(zkrp_verify, m)?)?;
    m.add_function(wrap_pyfunction!(gen_random_value, m)?)?;
    m.add_function(wrap_pyfunction!(zkrp_prove_mul, m)?)?;
    m.add_function(wrap_pyfunction!(zkrp_verify_mul, m)?)?;
    Ok(())
}