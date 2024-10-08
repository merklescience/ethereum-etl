#!/usr/bin/bash
source /root/ethereum-etl/env/bin/activate
ethereumetl stream --provider-uri $ETHEREUM_PROVIDER_URI -w 5 -B 3 -b 3 --period-seconds 2 -l /root/ethereum-etl/last_synced_block_hot.txt --lag 1 -e transaction,token_transfer,trace -o kafka -t producer-ethereum -ts hot