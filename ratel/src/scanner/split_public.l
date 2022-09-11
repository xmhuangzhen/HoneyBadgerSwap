%option noyywrap

%{


#include <string>

using namespace std;

bool finalizeOnChain;

string textPublic;
bool otherParameters, isConstructorHead, isConstructorBody;

int braces;


%}

SPACE [ \t\r]*

%%

.*constructor{SPACE}\( {
    //textPublic += "    event NewServer(address server);\n";
    textPublic += "    uint public N;\n";
    textPublic += "    uint public T;\n";
    textPublic += "    mapping (address => bool) public isServer;\n";
    //textPublic += "    mapping (address => uint) public votes;\n";
    //textPublic += "    mapping (address => mapping (address => bool)) voted;\n";
    textPublic += "\n";

    textPublic += "    uint public taskCnt;\n";
    textPublic += "    mapping (uint => string) public opEvent;\n";
    textPublic += "    mapping (uint => bytes) public opContent;\n";
    textPublic += "\n";

    //textPublic += "    event GenInputMask(uint inputMaskCnt, uint committeeChangeCnt);\n";
    //textPublic += "    uint public isInputMaskReady;\n";
    //textPublic += "    uint public committeeChangeCnt;\n";
    //textPublic += "    mapping (address => uint) public numCommittee;\n";
    //textPublic += "\n";

    textPublic += "\n";

    textPublic += string(yytext);
    isConstructorHead = true;
}

\) {
    if (isConstructorHead) {
        if (otherParameters) {
            otherParameters = false;
            textPublic += ", ";
        }

        textPublic += "address[] memory servers, uint threshold";
        isConstructorHead = false;
        isConstructorBody = true;
    }
    textPublic += string(yytext);
}

\{ {
    braces++;
    textPublic += string(yytext);
}

\} {
    braces--;
    if (braces == 1 && isConstructorBody) {
        textPublic += "\n";

        textPublic += "        N = servers.length;\n";
        //textPublic += "        isInputMaskReady = N;\n";
        textPublic += "        T = threshold;\n";
        textPublic += "        require(T <= N / 2);\n";
        textPublic += "        for (uint i = 0; i < servers.length; i++) {\n";
        textPublic += "            isServer[servers[i]] = true;\n";
        //textPublic += "            votes[servers[i]] = N;\n";
        //textPublic += "            for (uint j = 0; j < servers.length; j++) {\n";
        //textPublic += "                voted[servers[i]][servers[j]] = true;\n";
        //textPublic += "            }\n";
        textPublic += "        }\n";
        textPublic += "    ";
        isConstructorBody = false;
        textPublic += string(yytext);
        textPublic += "\n";
        textPublic += "\n";
        textPublic += "\n";

        textPublic += "    modifier onlyServer() {\n";
        textPublic += "        require(isServer[msg.sender], \"not an authorized party\");\n";
        textPublic += "        _;\n";
        textPublic += "    }\n";
        textPublic += "\n";
        textPublic += "\n";

        textPublic += "    event AddServer();\n";
        textPublic += "    function addServer(address server) public {\n";
        textPublic += "        // TODO: provide & verify agreement proof of majority of servers\n";
        textPublic += "        isServer[server] = true;\n";
        textPublic += "        N++;\n";
        textPublic += "        emit AddServer();\n";
        textPublic += "    }\n";
        textPublic += "\n";
        textPublic += "\n";

//        textPublic += "    function registerServer() public {\n";
        //textPublic += "        address server = msg.sender;\n";
        //textPublic += "        require(!isServer[server]);\n";
        //textPublic += "        emit NewServer(server);\n";
        //textPublic += "    }\n";
        //textPublic += "\n";
        //textPublic += "\n";

        //textPublic += "    function addServer(address s) public {\n";
        //textPublic += "        address server = msg.sender;\n";
        //textPublic += "        require(isServer[server]);\n";
        //textPublic += "        require(!voted[server][s]);\n";
        //textPublic += "        voted[server][s] = true;\n";
        //textPublic += "        votes[s] += 1;\n";
        //textPublic += "        if (votes[s] > T && !isServer[s]) {\n";
        //textPublic += "            isServer[s] = true;\n";
        //textPublic += "            N += 1;\n";
        //textPublic += "            isInputMaskReady = 0;\n";
        //textPublic += "            committeeChangeCnt += 1;\n";
        //textPublic += "            emit GenInputMask(inputMaskCnt, committeeChangeCnt);\n";
        //textPublic += "        }\n";
        //textPublic += "    }\n";
        //textPublic += "\n";
        //textPublic += "\n";

        //textPublic += "    function setReady(uint num) public {\n";
        //textPublic += "        address server = msg.sender;\n";
        //textPublic += "        require(isServer[server]);\n";
        //textPublic += "        if (numCommittee[server] < num) {\n";
        //textPublic += "            numCommittee[server] = num;\n";
        //textPublic += "            isInputMaskReady += 1;\n";
        //textPublic += "        }\n";
        //textPublic += "    }\n";
        //textPublic += "\n";
        //textPublic += "\n";

        //textPublic += "    function resetThreshold() public {\n";
        //textPublic += "    }\n";
        //textPublic += "\n";
        //textPublic += "\n";

        //textPublic += "    function removeServer(address s) public {\n";
        //textPublic += "        address server = msg.sender;\n";
        //textPublic += "        require(isServer[server]);\n";
        //textPublic += "        require(voted[server][s]);\n";
        //textPublic += "        voted[server][s] = false;\n";
        //textPublic += "        votes[s] -= 1;\n";
        //textPublic += "        if (votes[s] <= T) {\n";
        //textPublic += "            isServer[s] = false;\n";
        //textPublic += "            N -= 1;\n";
        //textPublic += "        }\n";
        //textPublic += "    }\n";
        //textPublic += "\n";
        //textPublic += "\n";

        if (finalizeOnChain) {
            textPublic += "    event Finalization(uint seq, uint finalizationSeq);\n";
            textPublic += "    mapping (uint => uint) public voteFinalization;\n";
            textPublic += "    mapping (uint => mapping (address => bool)) public votedFinalization;\n";
            textPublic += "    uint public finalizedTaskCnt;\n";
            textPublic += "    mapping (uint => uint) public finalized;\n";
            textPublic += "    function finalize(uint seq) public onlyServer {\n";
            textPublic += "        address server = msg.sender;\n";
            textPublic += "        require(!votedFinalization[seq][server] && finalized[seq] == 0);\n";
            textPublic += "        votedFinalization[seq][server] = true;\n";
            textPublic += "        voteFinalization[seq] += 1;\n";
            textPublic += "        if (voteFinalization[seq] > T) {\n";
            textPublic += "            uint finalizationSeq = ++finalizedTaskCnt;\n";
            textPublic += "            finalized[seq] = finalizationSeq;\n";
            textPublic += "            emit Finalization(seq, finalizationSeq);\n";
            textPublic += "        }\n";
            textPublic += "    }\n";
            textPublic += "\n\n";
        }

        textPublic += "    event ReserveInputMask(uint[] inputMaskIndexes);\n";
        textPublic += "    mapping (uint => address) public inputMaskOwner;\n";
        textPublic += "    function reserveInput(uint num) public {\n";
        textPublic += "        require(numTotalInputMask - numUsedInputMask >= num, \"Shortage of available input masks. Retry later!\");\n";
        textPublic += "        address user = msg.sender;\n";
        textPublic += "        uint[] memory inputMaskIndexes = new uint[](num);\n";
        textPublic += "        for (uint i = 0; i < num; i++) {\n";
        textPublic += "            uint inputMaskIdx = ++numUsedInputMask;\n";
        textPublic += "            inputMaskOwner[inputMaskIdx] = user;\n";
        textPublic += "            inputMaskIndexes[i] = inputMaskIdx;\n";
        textPublic += "        }\n";
        textPublic += "        emit ReserveInputMask(inputMaskIndexes);\n";
        textPublic += "    }\n";
        textPublic += "\n";
        textPublic += "\n";

        textPublic += "    event InitGenInputMask(bool refill, uint version);\n";
        textPublic += "    event FinalizeGenInputMask(uint numInputMask, uint lastInputMaskIndex);\n";
        textPublic += "    uint public versionInputMask;\n";
        textPublic += "    uint public numUsedInputMask;\n";
        textPublic += "    uint public numTotalInputMask;\n";
        textPublic += "    function initGenInputMask(bool refill) public onlyServer {\n";
        textPublic += "        // TODO: provide & verify agreement proof of majority of servers\n";
        textPublic += "        emit InitGenInputMask(refill, ++versionInputMask);\n";
        textPublic += "    }\n";
        textPublic += "    \n";
        textPublic += "    \n";
        textPublic += "    function finalizeGenInputMask(bool refill, uint num) public onlyServer{\n";
        textPublic += "        // TODO: provide & verify agreement proof of majority of servers\n";
        textPublic += "        if (!refill) {\n";
        textPublic += "            numTotalInputMask += num;\n";
        textPublic += "        } else {\n";
        textPublic += "            numTotalInputMask = numUsedInputMask + num;\n";
        textPublic += "        }\n";
        textPublic += "        emit FinalizeGenInputMask(num, numTotalInputMask);\n";
        textPublic += "    }\n";
        textPublic += "\n";
        textPublic += "\n";

        textPublic += "    event GenStateMask(address server, uint initStateMaskIndex, uint num);\n";
        textPublic += "    event RecoverState(uint seqRecoverState);\n";
        textPublic += "    mapping (address => uint) public numTotalStateMask;\n";
        textPublic += "    mapping (address => uint) public numUsedStateMask;\n";
        textPublic += "    mapping (address => uint) public cntRecoverState;\n";
        textPublic += "    mapping (address => mapping (uint => uint)) public initIndexRecoverState;\n";
        textPublic += "    mapping (address => mapping (uint => uint)) public numRecoverState;\n";
        textPublic += "    function genStateMask(uint num) public onlyServer {\n";
        textPublic += "        address server = msg.sender;\n";
        textPublic += "        emit GenStateMask(server, numTotalStateMask[server], num);\n";
        textPublic += "        numTotalStateMask[server] += num;\n";
        textPublic += "    }\n";
        textPublic += "\n";
        textPublic += "\n";
        textPublic += "    function consumeStateMask(uint num) public onlyServer {\n";
        textPublic += "        address server = msg.sender;\n";
        textPublic += "        require(numTotalStateMask[server] - numUsedStateMask[server] >= num, \"not enough state mask to consume\");\n";
        textPublic += "        emit RecoverState(++cntRecoverState[server]);\n";
        textPublic += "        initIndexRecoverState[server][cntRecoverState[server]] = numUsedStateMask[server];\n";
        textPublic += "        numRecoverState[server][cntRecoverState[server]] = num;\n";
        textPublic += "        numUsedStateMask[server] += num;\n";
        textPublic += "    }";

    } else textPublic += string(yytext);
}

. {
    if (isConstructorHead) {
        otherParameters = true;
    }
    textPublic += string(yytext);
}

\n {
    textPublic += string(yytext);
}

%%

int main(int argc, char **argv) {

    finalizeOnChain = argv[2][0] - '0';

	yylex();

    FILE *solFp;
    solFp = fopen("contracts/tmp.sol", "w");
    fprintf(solFp, "%s", textPublic.c_str());
    fclose(solFp);

	return 0;
}