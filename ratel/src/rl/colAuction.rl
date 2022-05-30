pragma solidity ^0.5.0;

import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

contract colAuction{
    using SafeMath for uint;
    using SafeERC20 for IERC20;

    address constant public ETH_addr = 0x0000000000000000000000000000000000000000;
    uint public colAuctionCnt;

    mapping (uint => uint) public biddersCnt;

    mapping (uint => uint) public curPriceList;
    mapping (uint => uint) public floorPriceList;
    mapping (uint => uint) public startPriceList;
    mapping (uint => uint) public totalAmtList;
    mapping (uint => address) public tokenAddrList;
    mapping (uint => address) public appAddrList;
    mapping (uint => address) public creatorAddrList;
    
    mapping (uint => uint) public checkTime;

    mapping (uint => uint) public status; // closed-1 created-2 submitted --- bidders_num+2 
   

    constructor() public {}

    function createAuction(uint StartPrice, uint FloorPrice, uint totalAmt, address token, address appAddr) public{
        uint colAuctionId = ++colAuctionCnt;
        curPriceList[colAuctionId] = StartPrice;
        floorPriceList[colAuctionId] = FloorPrice;
        startPriceList[colAuctionId] = StartPrice;
        totalAmtList[colAuctionId] = totalAmt;

        checkTime[colAuctionId] = block.number;

        status[colAuctionId] = 2;

        tokenAddrList[colAuctionId] = token;
        appAddrList[colAuctionId] = appAddr;
        creatorAddrList[colAuctionId] = msg.sender;
    }

    function scheduleCheck(uint colAuctionId) public {
        uint lastTime = checkTime[colAuctionId];
        uint curTime = block.number;
        require(lastTime + 10 < curTime);
        checkTime[colAuctionId] = block.number;

        uint curPrice = curPriceList[colAuctionId]*(50-curTime+lastTime)/50;
        curPriceList[colAuctionId] = curPrice;

        uint FloorPrice = floorPriceList[colAuctionId];
        uint totalAmt = totalAmtList[colAuctionId];

        address token_addr = tokenAddrList[colAuctionId];
        address appAddr = appAddrList[colAuctionId];
        address creatorAddr = creatorAddrList[colAuctionId];

        uint n = biddersCnt[colAuctionId];

        mpc(uint colAuctionId, uint n, uint curPrice, uint FloorPrice, uint totalAmt, address token_addr, address appAddr, address creatorAddr, address ETH_addr){

            cur_token_creator_balance = readDB(f'balanceBoard_{token_addr}_{creatorAddr}',int)
            cur_token_app_balance = readDB(f'balanceBoard_{token_addr}_{appAddr}',int)
            cur_eth_creator_balance = readDB(f'balanceBoard_{ETH_addr}_{creatorAddr}',int)

            import time
            add_benchmark_res_info = ''

            if curPrice < FloorPrice:
                for i in range(n):
                    vi,pricei,Pi,Amti = await runCheckFail(server, token_addr, i, colAuctionId)
                    await runCheckFailUpdate(server, token_addr, i, colAuctionId,vi,pricei,Pi,Amti)

                print(colAuctionId,'Auction failed!!!!!!!!!')

                add_benchmark_res_info = 'auctionFailed\t colAuctionId\t' + str(colAuctionId) +'\t'

                curStatus = 1
                set(status, uint curStatus, uint colAuctionId)
            
            else:
                amtSold = 0

                for i in range(n):
                    amtSold = await runCheckAuction(server, i, colAuctionId,amtSold,totalAmt,curPrice)

                mpcInput(sint amtSold, sint totalAmt,sint cur_eth_creator_balance,sint curPrice,sint totalAmt)
                
                v1 = amtSold.greater_equal(totalAmt,bit_length = bit_length)
                v2 = cur_eth_creator_balance.greater_equal(curPrice*totalAmt,bit_length=bit_length)

                print_ln('**** amtSold, totalAmt, v1, v2: %s %s %s %s',amtSold.reveal(),totalAmt.reveal(),v1.reveal(),v2.reveal())
                print_ln('cur_eth_creator_balance, curPrice, totalAmt: %s %s %s',cur_eth_creator_balance.reveal(),curPrice.reveal(),totalAmt.reveal())

                aucDone = v1*v2
                aucDone = aucDone.reveal()
                mpcOutput(cint aucDone)

                if aucDone == 1:
                    curAmt = 0
                    app_token_amt = 0

                    for i in range(n):
                        vi, pricei, Pi, Amti = await runCheckSuccess(server, i, colAuctionId)
                        curAmt, app_token_amt = await runCheckSuccessUpdate(server, i, colAuctionId, token_addr, ETH_addr, curPrice, curAmt, app_token_amt,vi,pricei,Pi,Amti)
                    mpcInput(sint cur_token_creator_balance,sint curPrice,sint totalAmt)

                    cur_token_creator_balance = cur_token_creator_balance + curPrice*totalAmt
                    
                    mpcOutput(sint cur_token_creator_balance)
                    

                    mpcInput(sint cur_token_app_balance,sint app_token_amt)
                    
                    cur_token_app_balance = cur_token_app_balance - app_token_amt
                    
                    mpcOutput(sint cur_token_app_balance)

                    add_benchmark_res_info = 'auctionSuccess\t colAuctionId\t' + str(colAuctionId) +'\t'


                    print(colAuctionId,'Auction success!!!!!!!!!')
                    curStatus = 1
                    set(status, uint curStatus, uint colAuctionId)

            writeDB(f'balanceBoard_{ETH_addr}_{creatorAddr}',cur_eth_creator_balance,int)
            writeDB(f'balanceBoard_{token_addr}_{creatorAddr}',cur_token_creator_balance,int)
            writeDB(f'balanceBoard_{token_addr}_{appAddr}',cur_token_app_balance,int)

            if add_benchmark_res_info != '':
                cur_time = time.strftime("%D %H:%M:%S",time.localtime())
                with open(f'ratel/benchmark/data/latency.csv', 'a') as f:
                    f.write(f'{add_benchmark_res_info}\t'
                            f'cur_time\t{cur_time}\n')

        }
    }

    pureMpc checkAuction(server, i, colAuctionId,amtSold,totalAmt,curPrice) {
        bids = readDB(f'bidsBoard_{colAuctionId}_{i+1}', dict)

        Xi = bids['price']
        Pi = bids['address']
        Amti = bids['amt']
        vi = bids['valid']

        print('colAuctionId: ',colAuctionId)

        mpcInput(sint Xi, sint curPrice, sint Amti, sint amtSold, sint totalAmt,sint vi)
        valid = (curPrice.less_equal(Xi,bit_length = bit_length))
        delta_amt = Amti*valid*vi
        new_amtSold = amtSold + delta_amt

        print_ln('valid Amti vi delta_amt, new_amtSold: %s %s %s %s %s',valid.reveal(),Amti.reveal(),vi.reveal(),delta_amt.reveal(),new_amtSold.reveal())

        mpcOutput(sint new_amtSold)

        return new_amtSold
    }

    pureMpc checkFail(server, token_addr, i, colAuctionId) {
        bids = readDB(f'bidsBoard_{colAuctionId}_{i+1}', dict)
    
        vi = bids['valid']
        pricei = bids['price']
        Pi = bids['address']
        Amti = bids['amt']

        return vi,pricei,Pi,Amti
    } 

    pureMpc checkFailUpdate(server, token_addr, i, colAuctionId,vi,pricei,Pi,Amti) {
        cur_token_balance = readDB(f'balanceBoard_{token_addr}_{Pi}',int)

        mpcInput(sint cur_token_balance,sint pricei,sint Amti,sint vi)
        cur_token_balance = cur_token_balance + vi*pricei*Amti
        mpcOutput(sint cur_token_balance)

        writeDB(f'balanceBoard_{token_addr}_{Pi}',cur_token_balance,int)
    }

    pureMpc checkSuccess(server, i, colAuctionId) {
        bids = readDB(f'bidsBoard_{colAuctionId}_{i+1}', dict)

        vi = bids['valid']
        pricei = bids['price']
        Pi = bids['address']
        Amti = bids['amt']

        return vi, pricei, Pi, Amti
    }

    pureMpc checkSuccessUpdate(server, i, colAuctionId, token_addr, ETH_addr, curPrice, curAmt, app_token_amt,vi,pricei,Pi,Amti){
        
        cur_eth_balance = readDB(f'balanceBoard_{ETH_addr}_{Pi}',int)
        cur_token_balance = readDB(f'balanceBoard_{token_addr}_{Pi}',int)

        mpcInput(sint cur_eth_balance,sint cur_token_balance,sint pricei,sint vi,sint curPrice,sint curAmt,sint Amti,sint app_token_amt)
        v1 = (curAmt.greater_equal(Amti,bit_length=bit_length)) 
        realAmt = vi*v1*Amti + vi*(1-v1)*curAmt
        cur_eth_balance = cur_eth_balance + realAmt
        cur_token_balance = cur_token_balance + pricei*Amti - curPrice*realAmt
        curAmt -= realAmt
        app_token_amt = app_token_amt + vi*Amti*pricei
        mpcOutput(sint curAmt,sint cur_eth_balance,sint cur_token_balance,sint app_token_amt)

        writeDB(f'balanceBoard_{ETH_addr}_{Pi}',cur_eth_balance,int)
        writeDB(f'balanceBoard_{token_addr}_{Pi}',cur_token_balance,int)
    
        return curAmt, app_token_amt
    }

    function initClient(address token_addr) public{
        address user_addr = msg.sender;
        mpc(address user_addr,address token_addr){
            init_balance = 100000
            writeDB(f'balanceBoard_{token_addr}_{user_addr}',init_balance,int)
        }
    }

    function submitBids(uint colAuctionId, $uint price, $uint Amt) public {
        address P = msg.sender;

        uint bidders_id = biddersCnt[colAuctionId]+1;
        biddersCnt[colAuctionId] = bidders_id;

        uint FloorPrice = floorPriceList[colAuctionId];

        address token_addr = tokenAddrList[colAuctionId];
        address appAddr = appAddrList[colAuctionId];

        mpc(uint colAuctionId, uint bidders_id, uint FloorPrice, $uint price, address P, $uint Amt, address token_addr, address appAddr){
            cur_token_balance = readDB(f'balanceBoard_{token_addr}_{P}',int)
            cur_app_balance = readDB(f'balanceBoard_{token_addr}_{appAddr}',int)

            mpcInput(sint cur_token_balance,sint cur_app_balance,sint price,sint Amt)
            valid = cur_token_balance.greater_equal(price*Amt,bit_length=bit_length)
            cur_token_balance = cur_token_balance - valid*price*Amt
            cur_app_balance = cur_app_balance + valid*price*Amt
            mpcOutput(sint valid,sint cur_token_balance,sint cur_app_balance)

            bid = {
                'price': price,
                'amt': Amt,
                'address': P,
                'valid':valid,
            }

            writeDB(f'bidsBoard_{colAuctionId}_{bidders_id}',bid,dict)
            writeDB(f'balanceBoard_{token_addr}_{P}',cur_token_balance,int)
            writeDB(f'balanceBoard_{token_addr}_{appAddr}',cur_app_balance,int)
            
            curStatus = bidders_id+2
            set(status, uint curStatus, uint colAuctionId)

            import time
            cur_time = time.strftime("%D %H:%M:%S",time.localtime())
            with open(f'ratel/benchmark/data/latency.csv', 'a') as f:
                f.write(f'submit_bid\t'
                        f'colAuctionId\t{colAuctionId}\t'
                        f'bidders_id\t{bidders_id}\t'
                        f'cur_time\t{cur_time}\n')
        
        }
    }


}

