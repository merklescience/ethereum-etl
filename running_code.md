Uninstall 

`pip3 uninstall ethereumetl`

Run setup.py 

`sudo python setup.py sdist`

Install ethereum-etl

`pip3 install dist/ethereum-etl-1.3.2.tar.gz`

Running the streaming locally

`ethereumetl stream --provider-uri <provider_uri> -w 5 -B 3 -b 3 --period-seconds 2 -l last_synced_block_hot.txt -e transaction,token_transfer,trace`
