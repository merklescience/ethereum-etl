#!/usr/bin/bash
source /root/ethereum-etl/env/bin/activate
python /root/ethereum-etl/ethereumetl.py stream --provider-uri $ETHEREUM_PROVIDER_URI -w 5 -B 3 -b 3 --period-seconds 1 -l /root/ethereum-etl/last_synced_block_warm.txt --lag 18 -e transaction,token_transfer,trace -o kafka -t producer-ethereum - ts hot