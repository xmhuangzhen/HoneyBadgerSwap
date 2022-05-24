pragma solidity ^0.5.0;

import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

contract colAuction{
    using SafeMath for uint;
    using SafeERC20 for IERC20;

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
    mapping (address => uint) public statusValue;
    mapping (uint => uint) public statusCount;


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

        uint curPrice = curPriceList[colAuctionId]*(100-curTime+lastTime)/100;
        curPriceList[colAuctionId] = curPrice;

        uint FloorPrice = floorPriceList[colAuctionId];
        uint totalAmt = totalAmtList[colAuctionId];

        address token_addr = tokenAddrList[colAuctionId];
        address appAddr = appAddrList[colAuctionId];
        address creatorAddr = creatorAddrList[colAuctionId];

        uint n = biddersCnt[colAuctionId];

        mpc(uint colAuctionId, uint n, uint curPrice, uint FloorPrice, uint totalAmt, address token_addr, address appAddr, address creatorAddr){

            cur_token_creator_balance = readDB(f'balanceBoard_{token_addr}_{creatorAddr}',int)
            cur_token_app_balance = readDB(f'balanceBoard_{token_addr}_{appAddr}',int)
            cur_eth_creator_balance = readDB(f'balanceBoard_{0}_{creatorAddr}',int)

            if curPrice < FloorPrice:
                print(colAuctionId,'Auction failed!!!!!!!!!')

                curStatus = 1
                set(status, uint curStatus, uint colAuctionId)
            
            else:
                n = len(bids)
                amtSold = 0

                aucDone = 0

                if aucDone == 1:
                    print(colAuctionId,'Auction success!!!!!!!!!')
                    curStatus = 1
                    set(status, uint curStatus, uint colAuctionId)

            writeDB(f'balanceBoard_{0}_{creatorAddr}',cur_eth_creator_balance,int)
            writeDB(f'balanceBoard_{token_addr}_{creatorAddr}',cur_token_creator_balance,int)
            writeDB(f'balanceBoard_{token_addr}_{appAddr}',cur_token_app_balance,int)
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
        }
    }
}
