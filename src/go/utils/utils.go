package utils

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"github.com/ethereum/go-ethereum"
	"github.com/ethereum/go-ethereum/accounts/abi/bind"
	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/core/types"
	"github.com/ethereum/go-ethereum/ethclient"
	"io/ioutil"
	"log"
	"math/big"
	"net"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

var (
	GOPATH     = os.Getenv("GOPATH")
	KEYSTORE   = os.Getenv("POA_KEYSTORE")
	minBalance = big.NewInt(300000000000000000)

	//// parameter for private net
	chainID = "123"
	//HttpEndpoint = "http://127.0.0.1:8545"
	EthPort = 8545
	//WsEndpoint   = "ws://127.0.0.1:8546"
	EthWsPort  = 8546
	EthAddr    = common.HexToAddress("0x0000000000000000000000000000000000000000")
	HbswapAddr = common.HexToAddress("0xF74Eb25Ab1785D24306CA6b3CBFf0D0b0817C5E2")
	TokenAddrs = []common.Address{
		common.HexToAddress("0x6b5c9637e0207c72Ee1a275b6C3b686ba8D87385"),
		common.HexToAddress("0x8C89e5D2bCc0e4C26E3295d48d052E11bd03C06A"),
	}

	// parameter for kovan test net
	//chainID			= "42"
	//HttpEndpoint	= "https://kovan.infura.io/v3/6a82d2519efb4d748c02552e02e369c1"
	//WsEndpoint		= "wss://kovan.infura.io/ws/v3/6a82d2519efb4d748c02552e02e369c1"
	//EthAddr 		= common.HexToAddress("0x0000000000000000000000000000000000000000")
	//HbswapAddr 		= common.HexToAddress("0x77527db365ec8de2296d33464224e045bd7882c8")
	//TokenAddrs 		= []common.Address{
	//	common.HexToAddress("0x63e7f20503256ddcfec64872aadb785d5a290cbb"),
	//	common.HexToAddress("0x403b0f962566ffb960d0de98875dc09603aa67e9"),
	//}
)

func ExecCmd(cmd *exec.Cmd) string {
	fmt.Printf("Cmd:\n====================\n%v\n====================\n", cmd)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	err := cmd.Run()
	if err != nil {
		fmt.Printf("err:\n%s\n", stderr.String())
		log.Fatalf("cmd.Run() failed with %s\n", err)
	}
	fmt.Printf("Output:\n====================\n%s====================\n", stdout.String())
	return stdout.String()
}

func StrToBig(st string) *big.Int {
	v, _ := new(big.Int).SetString(st, 10)
	return v
}

func GetEthClient(ethInstance string) *ethclient.Client {
	conn, err := ethclient.Dial(ethInstance)
	if err != nil {
		log.Fatal(err)
	}

	return conn
}

func GetAccount(account string) *bind.TransactOpts {
	dir := filepath.Join(KEYSTORE, account)
	//dir := GOPATH + "/src/github.com/initc3/MP-SPDZ/Scripts/hbswap/poa/keystore/" + account + "/"

	list, err := ioutil.ReadDir(dir)
	if err != nil {
		log.Printf("Error reading directory %s", dir)
		log.Fatal(err)
	}

	var name string
	for _, info := range list {
		name = info.Name()
		if err != nil {
			log.Fatal(err)
		}
	}

	//bytes, err := ioutil.ReadFile(dir + name)
	bytes, err := ioutil.ReadFile(filepath.Join(dir, name))
	if err != nil {
		log.Fatal(err)
	}

	password := ""
	auth, err := bind.NewTransactor(strings.NewReader(string(bytes)), password)
	if err != nil {
		log.Fatal(err)
	}

	auth.GasLimit = 8000000

	return auth
}

func WaitMined(ctx context.Context, ec *ethclient.Client,
	tx *types.Transaction, blockDelay uint64) (*types.Receipt, error) {
	const missingFieldErr = "missing required field 'transactionHash' for Log"

	if ec == nil {
		return nil, errors.New("nil ethclient")
	}
	queryTicker := time.NewTicker(time.Second)
	defer queryTicker.Stop()
	txHashBytes := common.HexToHash(tx.Hash().Hex())
	for {
		receipt, rerr := ec.TransactionReceipt(ctx, txHashBytes)
		if rerr == nil {
			if blockDelay == 0 {
				return receipt, rerr
			}
			break
		} else if rerr == ethereum.NotFound || rerr.Error() == missingFieldErr {
			select {
			case <-ctx.Done():
				return nil, ctx.Err()
			case <-queryTicker.C:
			}
		} else {
			return receipt, rerr
		}
	}
	ddl := big.NewInt(0)
	latestBlockHeader, err := ec.HeaderByNumber(ctx, nil)
	if err == nil {
		ddl.Add(new(big.Int).SetUint64(blockDelay), latestBlockHeader.Number)
	}
	for {
		latestBlockHeader, err := ec.HeaderByNumber(ctx, nil)
		if err == nil && ddl.Cmp(latestBlockHeader.Number) < 0 {
			receipt, rerr := ec.TransactionReceipt(ctx, txHashBytes)
			if rerr == nil {
				//fmt.Println("tx confirmed!")
				return receipt, rerr
			} else if rerr == ethereum.NotFound || rerr.Error() == missingFieldErr {
				return nil, errors.New("tx is dropped due to chain re-org")
			} else {
				return receipt, rerr
			}
		}
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-queryTicker.C:
		}
	}
}

func stringToBigInt(v string) *big.Int {
	value := big.NewInt(0)
	value.SetString(v, 10)
	return value
}

func GetIPAddr(hostname string) net.IP {
	addrs, err := net.LookupIP(hostname)
	if err != nil {
		fmt.Sprintf("Error looking up hostname %s", hostname)
		log.Fatal(err)
	}
	return addrs[0]
}

func GetURL(hostname string, port int, scheme string) string {
	addr := GetIPAddr(hostname)
	host := fmt.Sprintf("%s:%d", addr, port)
	u := &url.URL{
		Scheme: scheme,
		Host:   host,
	}
	return u.String()
}

func GetEthURL(hostname string) string {
	return GetURL(hostname, EthPort, "http")
}

func GetEthWsURL(hostname string) string {
	return GetURL(hostname, EthWsPort, "ws")
}

//func dbPut(key string, value []byte) {
//	mut.Lock()
//	db, _ := leveldb.OpenFile(fmt.Sprintf("Scripts/hbswap/db/server%s", serverID), nil)
//	err := db.Put([]byte(key), value, nil)
//	if err != nil {
//		fmt.Println("Error writing to database")
//	}
//	db.Close()
//	mut.Unlock()
//}

//func dbGet(key string) string {
//	mut.Lock()
//	db, _ := leveldb.OpenFile(fmt.Sprintf("Scripts/hbswap/db/server%s", serverID), nil)
//	data, err := db.Get([]byte(key), nil)
//	if err != nil {
//		fmt.Println("Error getting from database")
//	}
//	db.Close()
//	mut.Unlock()
//	return string(data)
//}
