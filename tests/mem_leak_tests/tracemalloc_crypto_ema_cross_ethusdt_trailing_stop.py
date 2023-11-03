#!/usr/bin/env python3
# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2023 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# -------------------------------------------------------------------------------------------------

from decimal import Decimal

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.engine import BacktestEngineConfig
from nautilus_trader.config.common import LoggingConfig
from nautilus_trader.examples.strategies.ema_cross_trailing_stop import EMACrossTrailingStop
from nautilus_trader.examples.strategies.ema_cross_trailing_stop import EMACrossTrailingStopConfig
from nautilus_trader.model.currencies import ETH
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.wranglers import TradeTickDataWrangler
from nautilus_trader.test_kit.fixtures.memory import snapshot_memory
from nautilus_trader.test_kit.providers import TestDataProvider
from nautilus_trader.test_kit.providers import TestInstrumentProvider


@snapshot_memory(5)
def run(*args, **kwargs):
    # Configure backtest engine
    config = BacktestEngineConfig(
        trader_id="BACKTESTER-001",
        logging=LoggingConfig(log_level="INFO", bypass_logging=True),
    )

    # Build the backtest engine
    engine = BacktestEngine(config=config)

    # Add a trading venue (multiple venues possible)
    BINANCE = Venue("BINANCE")
    engine.add_venue(
        venue=BINANCE,
        oms_type=OmsType.NETTING,
        account_type=AccountType.CASH,  # Spot CASH account (not for perpetuals or futures)
        base_currency=None,  # Multi-currency account
        starting_balances=[Money(1_000_000, USDT), Money(10, ETH)],
    )

    # Add instruments
    ETHUSDT_BINANCE = TestInstrumentProvider.ethusdt_binance()
    engine.add_instrument(ETHUSDT_BINANCE)

    # Add data
    provider = TestDataProvider()
    wrangler = TradeTickDataWrangler(instrument=ETHUSDT_BINANCE)
    ticks = wrangler.process(provider.read_csv_ticks("binance/ethusdt-trades.csv"))
    engine.add_data(ticks)

    # Configure your strategy
    config = EMACrossTrailingStopConfig(
        instrument_id=str(ETHUSDT_BINANCE.id),
        bar_type="ETHUSDT.BINANCE-100-TICK-LAST-INTERNAL",
        trade_size=Decimal("0.05"),
        fast_ema_period=10,
        slow_ema_period=20,
        atr_period=20,
        trailing_atr_multiple=3.0,
        trailing_offset_type="PRICE",
        trigger_type="LAST_TRADE",
    )
    # Instantiate and add your strategy
    strategy = EMACrossTrailingStop(config=config)
    engine.add_strategy(strategy=strategy)

    # Unnecessary for repeated runs
    # time.sleep(0.1)
    # input("Press Enter to continue...")

    # Run the engine (from start to end of data)
    engine.run()

    # Optionally view reports
    # with pd.option_context(
    #     "display.max_rows",
    #     100,
    #     "display.max_columns",
    #     None,
    #     "display.width",
    #     300,
    # ):
    #     print(engine.trader.generate_account_report(BINANCE))
    #     print(engine.trader.generate_order_fills_report())
    #     print(engine.trader.generate_positions_report())

    # For repeated backtest runs make sure to reset the engine
    engine.reset()

    # Good practice to dispose of the object
    engine.dispose()


if __name__ == "__main__":
    run()
