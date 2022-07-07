#!/usr/bin/bash
source env/bin/activate
python ethereumetl.py stream --provider-uri $ETHEREUM_PROVIDER_URI -w 5 -B 20 -b 5 --period-seconds 5 -l last_synced_block_warm.txt --lag 18 -e transaction,token_transfer,trace -o kafka -t eth.warm