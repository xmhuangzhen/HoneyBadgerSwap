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

        uint curPrice = curPriceList[colAuctionId]*(50-curTime+lastTime)/50;
        curPriceList[colAuctionId] = curPrice;

        uint FloorPrice = floorPriceList[colAuctionId];
        uint totalAmt = totalAmtList[colAuctionId];

        address token_addr = tokenAddrList[colAuctionId];
        address appAddr = appAddrList[colAuctionId];
        address creatorAddr = creatorAddrList[colAuctionId];

        uint n = biddersCnt[colAuctionId];

        mpc(uint colAuctionId, uint n, uint curPrice, uint FloorPrice, uint totalAmt, address token_addr, address appAddr, address creatorAddr){
            bids = readDB(f'bidsBoard_{colAuctionId}', list)


            if curPrice < FloorPrice:
                print(colAuctionId,'Auction failed!!!!!!!!!')

                curStatus = 1
                set(status, uint curStatus, uint colAuctionId)
            
            else:
                n = len(bids)
                amtSold = 0

                for i in range(n):
                    (Xi,Pi,Amti) = bids[i]

                    mpcInput(sint Xi, sint curPrice, sint Amti, sint amtSold, sint totalAmt)
                    valid = (curPrice.less_equal(Xi,bit_length = bit_length))
                    amtSold += Amti*valid
                    mpcOutput(sint amtSold)

                mpcInput(sint amtSold, sint totalAmt)
                aucDone = (amtSold.greater_equal(totalAmt,bit_length = bit_length).reveal())
                mpcOutput(cint aucDone)

                if aucDone == 1:
                    print(colAuctionId,'Auction success!!!!!!!!!')
                    curStatus = 1
                    set(status, uint curStatus, uint colAuctionId)

        }
    }

    function submitBids(uint colAuctionId, $uint price, $uint Amt) public {
        address P = msg.sender;

        uint bidders_id = biddersCnt[colAuctionId]+1;
        biddersCnt[colAuctionId] = bidders_id;

        uint FloorPrice = floorPriceList[colAuctionId];

        mpc(uint colAuctionId, uint bidders_id, uint FloorPrice, $uint price, address P, $uint Amt){
            bids = readDB(f'bidsBoard_{colAuctionId}', list)

            mpcInput(sint price, sint FloorPrice)
            valid = (price.greater_equal(FloorPrice, bit_length=bit_length)).reveal()
            mpcOutput(cint valid)

            if valid == 1:
                bids.append((price,P,Amt))
            writeDB(f'bidsBoard_{colAuctionId}',bids,list)
            
            curStatus = bidders_id+2
            set(status, uint curStatus, uint colAuctionId)
        }
    }
}
