#!/usr/bin/bash

rm last_synced_block_hot.txt

python ethereumetl.py stream --provider-uri $ETHEREUM_PROVIDER_URI -w 35 -B 20 -b 5 --period-seconds 1 -l last_synced_block_hot.txt -e transaction,token_transfer,trace -o kafka -t eth.hot