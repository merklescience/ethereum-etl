import logging

from blockchainetl.jobs.exporters.console_item_exporter import ConsoleItemExporter
from blockchainetl.jobs.exporters.in_memory_item_exporter import InMemoryItemExporter
from ethereumetl.enumeration.entity_type import EntityType
from ethereumetl.jobs.export_blocks_job import ExportBlocksJob
from ethereumetl.jobs.export_receipts_job import ExportReceiptsJob
from ethereumetl.jobs.export_traces_job import ExportTracesJob
from ethereumetl.jobs.extract_contracts_job import ExtractContractsJob
from ethereumetl.jobs.extract_token_transfers_job import ExtractTokenTransfersJob
from ethereumetl.jobs.extract_tokens_job import ExtractTokensJob
from ethereumetl.streaming.enrich import enrich_transactions, enrich_logs, enrich_token_transfers, enrich_traces, \
    enrich_contracts, enrich_tokens
from ethereumetl.streaming.eth_item_id_calculator import EthItemIdCalculator
from ethereumetl.thread_local_proxy import ThreadLocalProxy
from web3 import Web3


class EthStreamerAdapter:
    def __init__(
            self,
            batch_web3_provider,
            item_exporter=ConsoleItemExporter(),
            batch_size=100,
            max_workers=5,
            entity_types=tuple(EntityType.ALL_FOR_STREAMING)):
        self.batch_web3_provider = batch_web3_provider
        self.item_exporter = item_exporter
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.entity_types = entity_types
        self.item_id_calculator = EthItemIdCalculator()

    def open(self):
        self.item_exporter.open()

    def get_current_block_number(self):
        return int(Web3(self.batch_web3_provider).eth.getBlock("latest").number)

    def export_all(self, start_block, end_block):
        # Export blocks and transactions
        blocks, transactions = [], []
        if self._should_export(EntityType.BLOCK) or self._should_export(EntityType.TRANSACTION):
            blocks, transactions = self._export_blocks_and_transactions(start_block, end_block)

        # Export receipts and logs
        receipts, logs = [], []
        if self._should_export(EntityType.RECEIPT) or self._should_export(EntityType.LOG):
            receipts, logs = self._export_receipts_and_logs(blocks)

        # Extract token transfers
        token_transfers = []
        if self._should_export(EntityType.TOKEN_TRANSFER):
            token_transfers = self._extract_token_transfers(logs)

        # Export traces
        traces = []
        if self._should_export(EntityType.TRACE):
            traces = self._export_traces(start_block, end_block)

        # Export contracts
        contracts = []
        if self._should_export(EntityType.CONTRACT):
            contracts = self._export_contracts(traces)

        # Export tokens
        tokens = []
        if self._should_export(EntityType.TOKEN):
            tokens = self._extract_tokens(contracts)

        enriched_blocks = blocks \
            if EntityType.BLOCK in self.entity_types else []
        enriched_transactions = enrich_transactions(transactions, receipts) \
            if EntityType.TRANSACTION in self.entity_types else []
        enriched_logs = enrich_logs(blocks, logs) \
            if EntityType.LOG in self.entity_types else []
        enriched_token_transfers = enrich_token_transfers(blocks, token_transfers) \
            if EntityType.TOKEN_TRANSFER in self.entity_types else []
        enriched_traces = enrich_traces(blocks, traces) \
            if EntityType.TRACE in self.entity_types else []
        enriched_contracts = enrich_contracts(blocks, contracts) \
            if EntityType.CONTRACT in self.entity_types else []
        enriched_tokens = enrich_tokens(blocks, tokens) \
            if EntityType.TOKEN in self.entity_types else []

        logging.info('Exporting with ' + type(self.item_exporter).__name__)

        all_items = enriched_blocks + \
            enriched_transactions + \
            enriched_logs + \
            enriched_token_transfers + \
            enriched_traces + \
            enriched_contracts + \
            enriched_tokens

        self.calculate_item_ids(all_items)

        self.item_exporter.export_items(all_items)

    def _export_blocks_and_transactions(self, start_block, end_block):
        blocks_and_transactions_item_exporter = InMemoryItemExporter(item_types=['block', 'transaction'])
        blocks_and_transactions_job = ExportBlocksJob(
            start_block=start_block,
            end_block=end_block,
            batch_size=self.batch_size,
            batch_web3_provider=self.batch_web3_provider,
            max_workers=self.max_workers,
            item_exporter=blocks_and_transactions_item_exporter,
            export_blocks=self._should_export(EntityType.BLOCK),
            export_transactions=self._should_export(EntityType.TRANSACTION)
        )
        blocks_and_transactions_job.run()
        blocks = blocks_and_transactions_item_exporter.get_items('block')
        transactions = blocks_and_transactions_item_exporter.get_items('transaction')
        return blocks, transactions

