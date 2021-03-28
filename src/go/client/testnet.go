// go run /go/src/github.com/initc3/HoneyBadgerSwap/src/go/client/testnet.go

package main

import (
	"context"
	"fmt"
	"github.com/initc3/HoneyBadgerSwap/src/go/utils"
	"math/big"
)

func main() {
	conn := utils.GetEthClient(utils.TestnetWsEndpoint)
	//conn := utils.GetEthClient("http://127.0.0.1:8545")

	admin := utils.GetAccount(fmt.Sprintf("server_0"))

	//peer := utils.GetAccount(fmt.Sprintf("account_0"))
	//peer := utils.GetAccount(fmt.Sprintf("server_3"))
	//peer := common.HexToAddress("0xc33a4b5b609fcc294dca060347761226e78c0b7a")
	//peer := common.HexToAddress("0x3C19cA734eeaA2b3617C76afa993A54b5C6f6448")

	var balance *big.Int

	balance, _ = conn.BalanceAt(context.Background(), admin.From, nil)
	fmt.Printf("balance %v\n", balance)
	//
	//utils.FundETH(conn, peer, utils.StrToBig("1000000000000000000"))
	//
	//balance, _ = conn.BalanceAt(context.Background(), peer, nil)
	//fmt.Printf("balance %v\n", balance)

	//token := utils.TokenAddrs["testnet"][0]
	//balance = utils.GetBalanceToken(conn, peer, token)
	//fmt.Printf("balance %v\n", balance)
	//
	//utils.FundToken(conn, token, peer, big.NewInt(10000))
	//balance = utils.GetBalanceToken(conn, peer, token)
	//fmt.Printf("balance %v\n", balance)
}
