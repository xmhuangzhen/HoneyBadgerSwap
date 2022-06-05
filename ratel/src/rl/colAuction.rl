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
    mapping (uint => uint) public debtList;
    
    mapping (uint => uint) public checkTime;

    mapping (uint => uint) public status; // closed-1 created-2 submitted --- bidders_num+2 
   

    constructor() public {}

    function createAuction(uint StartPrice, uint FloorPrice, uint totalAmt, uint debt, address token, address appAddr, address creator_addr) public{
        uint colAuctionId = ++colAuctionCnt;
        curPriceList[colAuctionId] = StartPrice;
        floorPriceList[colAuctionId] = FloorPrice;
        startPriceList[colAuctionId] = StartPrice;
        totalAmtList[colAuctionId] = totalAmt;

        checkTime[colAuctionId] = block.number;

        status[colAuctionId] = 2;

        tokenAddrList[colAuctionId] = token;
        appAddrList[colAuctionId] = appAddr;
        creatorAddrList[colAuctionId] = creator_addr;
        debtList[colAuctionId] = debt;

        mpc(uint colAuctionId,uint debt){
            writeDB(f'debtBoard_{colAuctionId}',debt,int)
        }
    }

    function scheduleCheck(uint colAuctionId) public {
        uint lastTime = checkTime[colAuctionId];
        uint curTime = block.number;
        require(lastTime + 10 < curTime);
        checkTime[colAuctionId] = block.number;

        uint curPrice = curPriceList[colAuctionId]*(20000-curTime+lastTime)/20000;
        curPriceList[colAuctionId] = curPrice;

        uint FloorPrice = floorPriceList[colAuctionId];
        uint totalAmt = totalAmtList[colAuctionId];

        address token_addr = tokenAddrList[colAuctionId];
        address appAddr = appAddrList[colAuctionId];
        address creatorAddr = creatorAddrList[colAuctionId];

        uint n = biddersCnt[colAuctionId];

        uint debt = debtList[colAuctionId];

        mpc(uint colAuctionId, uint n, uint curPrice, uint FloorPrice, uint totalAmt, uint debt, address token_addr, address appAddr, address creatorAddr, address ETH_addr){

            import time
            times = []
            times.append(time.perf_counter())

            cur_token_creator_balance = readDB(f'balanceBoard_{token_addr}_{creatorAddr}',int)
            cur_token_app_balance = readDB(f'balanceBoard_{token_addr}_{appAddr}',int)
            cur_eth_creator_balance = readDB(f'balanceBoard_{ETH_addr}_{creatorAddr}',int)

            import time
            add_benchmark_res_info = ''

            if curPrice < FloorPrice:
    
                times.append(time.perf_counter())

                for i in range(n):
                    vi,pricei,Pi,Amti = await runCheckFail(server, token_addr, i, colAuctionId)
                    await runCheckFailUpdate(server, token_addr, i, colAuctionId,vi,pricei,Pi,Amti)

                times.append(time.perf_counter())

                print(colAuctionId,'Auction failed!!!!!!!!!')

                add_benchmark_res_info = 'auctionFailed\t colAuctionId\t' + str(colAuctionId) +'\t'

                curStatus = 1
                set(status, uint curStatus, uint colAuctionId)
            
                times.append(time.perf_counter())

            writeDB(f'balanceBoard_{ETH_addr}_{creatorAddr}',cur_eth_creator_balance,int)
            writeDB(f'balanceBoard_{token_addr}_{creatorAddr}',cur_token_creator_balance,int)
            writeDB(f'balanceBoard_{token_addr}_{appAddr}',cur_token_app_balance,int)

            if add_benchmark_res_info != '':
                cur_time = time.strftime("%D %H:%M:%S",time.localtime())
                with open(f'ratel/benchmark/data/latency.csv', 'a') as f:
                    f.write(f'{add_benchmark_res_info}\t'
                            f'cur_time\t{cur_time}\n')

                with open(f'ratel/benchmark/data/latency_{server.serverID}.csv', 'a') as f:
                    for op, t in enumerate(times):
                        f.write(f'auction end\t'
                                f'op\t{op + 1}\t'
                                f'cur_time\t{t}\n')


        }
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

        recover_debt = pricei*Amti
        actual_debt = recover_debt * vi

        cur_token_balance = cur_token_balance + actual_debt
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

    pureMpc checkSuccessUpdate(server, i, colAuctionId, token_addr, ETH_addr, curAmt,vi,pricei,Pi,Amti){
        
        cur_eth_balance = readDB(f'balanceBoard_{ETH_addr}_{Pi}',int)
        cur_token_balance = readDB(f'balanceBoard_{token_addr}_{Pi}',int)

        mpcInput(sint cur_eth_balance,sint cur_token_balance,sint pricei,sint vi,sint curAmt,sint Amti)
        
        v1 = (curAmt >= Amti)

        actAmt = vi*Amti
        realAmt1 = v1*actAmt
        realAmt2 = (1-v1)*actAmt
        realAmt = realAmt1 + realAmt2
        
        cur_eth_balance = cur_eth_balance + realAmt

        origin_recover_debt = pricei*Amti
        actual_recover_debt = pricei*realAmt

        cur_token_balance = cur_token_balance + origin_recover_debt - actual_recover_debt

        curAmt -= realAmt
        
        mpcOutput(sint curAmt,sint cur_eth_balance,sint cur_token_balance)

        writeDB(f'balanceBoard_{ETH_addr}_{Pi}',cur_eth_balance,int)
        writeDB(f'balanceBoard_{token_addr}_{Pi}',cur_token_balance,int)
    
        return curAmt
    }

    function initClient(address token_addr,address user_addr) public{
        mpc(address user_addr,address token_addr){
            init_balance = 10000000000
            writeDB(f'balanceBoard_{token_addr}_{user_addr}',init_balance,int)
        }
    }

    function submitBids(uint colAuctionId, $uint price, $uint Amt,address bidder_addr) public {
        address P = bidder_addr;

        uint bidders_id = biddersCnt[colAuctionId]+1;
        biddersCnt[colAuctionId] = bidders_id;

        address token_addr = tokenAddrList[colAuctionId];
        address appAddr = appAddrList[colAuctionId];
        address creatorAddr = creatorAddrList[colAuctionId]

        uint debt = debtList[colAuctionId];

        mpc(uint colAuctionId, uint bidders_id, $uint price, address P, $uint Amt,uint debt, address token_addr, address appAddr,address ETH_addr,address creatorAddr){
            times = []

            import time
            times.append(time.perf_counter())
            start_time = time.strftime("%D %H:%M:%S",time.localtime())

            cur_token_balance = readDB(f'balanceBoard_{token_addr}_{P}',int)
            cur_token_app_balance = readDB(f'balanceBoard_{token_addr}_{appAddr}',int)
            remain_debt = readDB(f'debtBoard_{colAuctionId}',int)
            cur_token_creator_balance = readDB(f'balanceBoard_{token_addr}_{creatorAddr}',int)
            cur_eth_creator_balance = readDB(f'balanceBoard_{ETH_addr}_{creatorAddr}',int)


            times.append(time.perf_counter())

            mpcInput(sint cur_token_balance,sint cur_token_app_balance,sint price,sint Amt,sint remain_debt)

            recover_debt = price*Amt
            valid = (cur_token_balance >= recover_debt)
            actual_debt = valid*recover_debt

            remain_debt = remain_debt - actual_debt
            cur_token_balance = cur_token_balance - actual_debt
            cur_token_app_balance = cur_token_app_balance + actual_debt

            aucDone = (remain_debt <= 0)
            aucDone = aucDone.reveal()

            print_ln('remain_debt %s',remain_debt.reveal())

            mpcOutput(sint valid,sint cur_token_balance,sint cur_token_app_balance,sint remain_debt,cint aucDone)

            times.append(time.perf_counter())

            bid = {
                'price': price,
                'amt': Amt,
                'address': P,
                'valid':valid,
            }

            times.append(time.perf_counter())

            curStatus = bidders_id+2

            if aucDone == 1:
                curStatus = 1
                for i in range(bidders_id):
                    vi, pricei, Pi, Amti = await runCheckSuccess(server, i, colAuctionId)
                    curAmt = await runCheckSuccessUpdate(server, i, colAuctionId, token_addr, ETH_addr, curAmt,vi,pricei,Pi,Amti)

                times.append(time.perf_counter())

                mpcInput(sint cur_token_creator_balance,sint debt)
                cur_token_creator_balance = cur_token_creator_balance + debt
                mpcOutput(sint cur_token_creator_balance)
                    
                times.append(time.perf_counter())

                mpcInput(sint cur_token_app_balance,sint debt)
                cur_token_app_balance = cur_token_app_balance - debt                
                mpcOutput(sint cur_token_app_balance)

                times.append(time.perf_counter())

                add_benchmark_res_info = 'auctionSuccess\t colAuctionId\t' + str(colAuctionId) +'\t'
                print(colAuctionId,'Auction success!!!!!!!!!')


            writeDB(f'bidsBoard_{colAuctionId}_{bidders_id}',bid,dict)
            writeDB(f'balanceBoard_{token_addr}_{P}',cur_token_balance,int)
            writeDB(f'balanceBoard_{token_addr}_{appAddr}',cur_token_app_balance,int)
            writeDB(f'bidsBoard_{colAuctionId}',remain_debt,int)
            writeDB(f'balanceBoard_{token_addr}_{creatorAddr}',cur_token_creator_balance,int)
            writeDB(f'balanceBoard_{ETH_addr}_{creatorAddr}',cur_eth_creator_balance,int)


            set(status, uint curStatus, uint colAuctionId)

            times.append(time.perf_counter())

            with open(f'ratel/benchmark/data/latency.csv', 'a') as f:
                f.write(f'submit_bid\t'
                        f'colAuctionId\t{colAuctionId}\t'
                        f'bidders_id\t{bidders_id}\t'
                        f'start_time\t{start_time}\n')
        
            with open(f'ratel/benchmark/data/latency_{server.serverID}.csv', 'a') as f:
                for op, t in enumerate(times):
                    f.write(f'submit_bid\t'
                            f'op\t{op + 1}\t'
                            f'cur_time\t{t}\n')

            if add_benchmark_res_info != '':
                cur_time = time.strftime("%D %H:%M:%S",time.localtime())
                with open(f'ratel/benchmark/data/latency.csv', 'a') as f:
                    f.write(f'{add_benchmark_res_info}\t'
                            f'cur_time\t{cur_time}\n')

                with open(f'ratel/benchmark/data/latency_{server.serverID}.csv', 'a') as f:
                    for op, t in enumerate(times):
                        f.write(f'{add_benchmark_res_info}\t'
                                f'op\t{op + 1}\t'
                                f'cur_time\t{t}\n')

        }
    }
}

