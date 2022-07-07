#!/usr/bin/bash

rm last_synced_block_warm.txt

python ethereumetl.py stream --provider-uri $PROVIDER_URI -w 5 -B 20 -b 5 --period-seconds 5 -l last_synced_block_warm.txt --lag 18 -e transaction,token_transfer,trace -o kafka -t eth.warm