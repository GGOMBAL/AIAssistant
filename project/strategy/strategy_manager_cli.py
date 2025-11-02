#!/usr/bin/env python3
"""
Strategy Manager CLI - Strategy Layer
전략 관리 커맨드 라인 도구

기능:
- 현재 활성 전략 확인
- 전략 전환
- 전략 비교
- 전략 설정 확인
"""

import sys
import os
from pathlib import Path
from typing import Optional
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from project.strategy.strategy_signal_config_loader import StrategySignalConfigLoader


class StrategyManagerCLI:
    """전략 관리 CLI"""

    def __init__(self):
        """Initialize CLI"""
        self.config_loader = StrategySignalConfigLoader()
        self.config_path = self.config_loader.config_path

    def display_menu(self):
        """메인 메뉴 표시"""
        print("\n" + "="*80)
        print("STRATEGY MANAGER - Multi-Strategy Trading System")
        print("="*80)
        print("\n[OPTIONS]")
        print("  1. Show Current Active Strategy")
        print("  2. List All Available Strategies")
        print("  3. Switch Strategy")
        print("  4. Compare Strategies")
        print("  5. Show Strategy Details")
        print("  0. Exit")
        print("\n" + "="*80)

    def show_current_strategy(self):
        """현재 활성 전략 표시"""
        active = self.config_loader.get_active_strategy()
        config = self.config_loader.get_strategy_config(active)

        print("\n" + "="*80)
        print(f"CURRENT ACTIVE STRATEGY: {active.upper()}")
        print("="*80)
        print(f"\nName: {config.get('name', 'N/A')}")
        print(f"Description: {config.get('description', 'N/A')}")
        print("\nKey Parameters:")

        # Fundamental Signal
        f_sig = config.get('fundamental_signal', {})
        print(f"\n  [Fundamental Signal]")
        print(f"    Enabled: {f_sig.get('enabled', False)}")
        if f_sig.get('enabled'):
            print(f"    Market Cap Min: ${f_sig.get('market_cap', {}).get('min', 0):,.0f}")
            print(f"    Revenue YoY Min: {f_sig.get('revenue', {}).get('min_yoy', 0)*100:.1f}%")
            print(f"    EPS YoY Min: {f_sig.get('eps', {}).get('min_yoy', 0)*100:.1f}%")

        # Weekly Signal
        w_sig = config.get('weekly_signal', {})
        print(f"\n  [Weekly Signal]")
        print(f"    Enabled: {w_sig.get('enabled', False)}")
        if w_sig.get('enabled'):
            print(f"    High Stability Factor: {w_sig.get('high_stability', {}).get('factor', 0):.2f}")
            print(f"    Low Distance Factor: {w_sig.get('low_distance', {}).get('factor', 0):.2f}")
            print(f"    High Distance Factor: {w_sig.get('high_distance', {}).get('factor', 0):.2f}")

        # RS Signal
        rs_sig = config.get('rs_signal', {})
        print(f"\n  [RS Signal]")
        print(f"    Enabled: {rs_sig.get('enabled', False)}")
        if rs_sig.get('enabled'):
            print(f"    RS Threshold: {rs_sig.get('threshold', 0)}")

        # Daily Signal
        d_sig = config.get('daily_signal', {})
        print(f"\n  [Daily Signal]")
        print(f"    Enabled: {d_sig.get('enabled', False)}")
        if d_sig.get('enabled'):
            print(f"    Losscut Ratio: {d_sig.get('prices', {}).get('losscut_ratio', 0):.2%}")
            timeframes = d_sig.get('breakout', {}).get('timeframes', [])
            print(f"    Breakout Timeframes: {', '.join(timeframes)}")

        print("\n" + "="*80)

    def list_strategies(self):
        """모든 전략 목록 표시"""
        strategies = self.config_loader.get_all_strategies()
        active = self.config_loader.get_active_strategy()

        print("\n" + "="*80)
        print("AVAILABLE STRATEGIES")
        print("="*80)

        for i, strategy_name in enumerate(strategies.keys(), 1):
            strategy_config = strategies[strategy_name]
            is_active = " [ACTIVE]" if strategy_name == active else ""

            print(f"\n{i}. {strategy_name.upper()}{is_active}")
            print(f"   Name: {strategy_config.get('name', 'N/A')}")
            print(f"   Description: {strategy_config.get('description', 'N/A')}")

            # Key parameters summary
            f_sig = strategy_config.get('fundamental_signal', {})
            w_sig = strategy_config.get('weekly_signal', {})
            rs_sig = strategy_config.get('rs_signal', {})

            min_cap = f_sig.get('market_cap', {}).get('min', 0)
            min_rev_yoy = f_sig.get('revenue', {}).get('min_yoy', 0)
            rs_threshold = rs_sig.get('threshold', 0)

            print(f"   Market Cap Min: ${min_cap/1e9:.1f}B | Revenue YoY: {min_rev_yoy*100:.0f}% | RS: {rs_threshold}")

        print("\n" + "="*80)

    def switch_strategy(self):
        """전략 전환"""
        strategies = list(self.config_loader.get_all_strategies().keys())
        active = self.config_loader.get_active_strategy()

        print("\n" + "="*80)
        print("SWITCH STRATEGY")
        print("="*80)
        print(f"\nCurrent Active Strategy: {active.upper()}")
        print("\nAvailable Strategies:")

        for i, strategy in enumerate(strategies, 1):
            marker = " [CURRENT]" if strategy == active else ""
            print(f"  {i}. {strategy}{marker}")

        print("\n0. Cancel")

        try:
            choice = input("\nSelect strategy number: ").strip()

            if choice == "0":
                print("Cancelled.")
                return

            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(strategies):
                new_strategy = strategies[choice_idx]

                # Confirm
                confirm = input(f"\nSwitch to '{new_strategy}'? (y/n): ").strip().lower()
                if confirm == 'y':
                    self._update_active_strategy(new_strategy)
                    print(f"\n[OK] Successfully switched to '{new_strategy}'")
                    print("[WARNING] Restart the application for changes to take effect.")
                else:
                    print("Cancelled.")
            else:
                print("[ERROR] Invalid choice.")

        except ValueError:
            print("[ERROR] Invalid input.")
        except Exception as e:
            print(f"[ERROR] Failed to switch strategy: {e}")

    def _update_active_strategy(self, new_strategy: str):
        """YAML 파일의 active_strategy 업데이트"""
        # Read current config
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Update active_strategy
        config['active_strategy'] = new_strategy

        # Write back
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def compare_strategies(self):
        """전략 비교"""
        print("\n" + "="*80)
        print("STRATEGY COMPARISON")
        print("="*80)

        strategies = self.config_loader.get_all_strategies()

        # Header
        print(f"\n{'Parameter':<30} {'Conservative':<15} {'Balanced':<15} {'Aggressive':<15}")
        print("-" * 80)

        # Market Cap Min
        row = "Market Cap Min"
        for strategy in ['conservative', 'balanced', 'aggressive']:
            if strategy in strategies:
                val = strategies[strategy].get('fundamental_signal', {}).get('market_cap', {}).get('min', 0)
                print(f"{row:<30} ${val/1e9:>12.1f}B", end=" ")
                row = ""
        print()

        # Revenue YoY Min
        row = "Revenue YoY Min"
        for strategy in ['conservative', 'balanced', 'aggressive']:
            if strategy in strategies:
                val = strategies[strategy].get('fundamental_signal', {}).get('revenue', {}).get('min_yoy', 0)
                print(f"{row:<30} {val*100:>13.0f}%", end=" ")
                row = ""
        print()

        # EPS YoY Min
        row = "EPS YoY Min"
        for strategy in ['conservative', 'balanced', 'aggressive']:
            if strategy in strategies:
                val = strategies[strategy].get('fundamental_signal', {}).get('eps', {}).get('min_yoy', 0)
                print(f"{row:<30} {val*100:>13.0f}%", end=" ")
                row = ""
        print()

        # High Stability Factor
        row = "High Stability Factor"
        for strategy in ['conservative', 'balanced', 'aggressive']:
            if strategy in strategies:
                val = strategies[strategy].get('weekly_signal', {}).get('high_stability', {}).get('factor', 0)
                print(f"{row:<30} {val:>14.2f}", end=" ")
                row = ""
        print()

        # RS Threshold
        row = "RS Threshold"
        for strategy in ['conservative', 'balanced', 'aggressive']:
            if strategy in strategies:
                val = strategies[strategy].get('rs_signal', {}).get('threshold', 0)
                print(f"{row:<30} {val:>14.0f}", end=" ")
                row = ""
        print()

        # Losscut Ratio
        row = "Losscut Ratio"
        for strategy in ['conservative', 'balanced', 'aggressive']:
            if strategy in strategies:
                val = strategies[strategy].get('daily_signal', {}).get('prices', {}).get('losscut_ratio', 0)
                print(f"{row:<30} {val:>13.2%}", end=" ")
                row = ""
        print()

        print("\n" + "="*80)
        print("\nStrategy Profiles:")
        print("  Conservative: Large cap (10B+), high growth (15%+), strict filters, 2% stop loss")
        print("  Balanced:     Mid cap (2B+), moderate growth (10%+), balanced risk, 3% stop loss")
        print("  Aggressive:   Small/mid cap (500M+), relaxed filters (5%+), 5% stop loss")
        print("="*80)

    def show_strategy_details(self):
        """전략 상세 정보 표시"""
        strategies = list(self.config_loader.get_all_strategies().keys())

        print("\n" + "="*80)
        print("STRATEGY DETAILS")
        print("="*80)
        print("\nAvailable Strategies:")

        for i, strategy in enumerate(strategies, 1):
            print(f"  {i}. {strategy}")

        print("\n0. Cancel")

        try:
            choice = input("\nSelect strategy number: ").strip()

            if choice == "0":
                return

            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(strategies):
                strategy_name = strategies[choice_idx]
                self._display_strategy_details(strategy_name)
            else:
                print("[ERROR] Invalid choice.")

        except ValueError:
            print("[ERROR] Invalid input.")

    def _display_strategy_details(self, strategy_name: str):
        """특정 전략의 상세 정보 표시"""
        config = self.config_loader.get_strategy_config(strategy_name)

        print("\n" + "="*80)
        print(f"STRATEGY DETAILS: {strategy_name.upper()}")
        print("="*80)
        print(f"\nName: {config.get('name', 'N/A')}")
        print(f"Description: {config.get('description', 'N/A')}")

        # Earnings Signal
        e_sig = config.get('earnings_signal', {})
        print(f"\n[Earnings Signal]")
        print(f"  Enabled: {e_sig.get('enabled', False)}")
        print(f"  Revenue Min Prev YoY: {e_sig.get('revenue', {}).get('min_prev_yoy', 0)*100:.1f}%")
        print(f"  Revenue Require Growth: {e_sig.get('revenue', {}).get('require_growth', False)}")
        print(f"  EPS Min Prev YoY: {e_sig.get('eps', {}).get('min_prev_yoy', 0)*100:.1f}%")
        print(f"  EPS Require Growth: {e_sig.get('eps', {}).get('require_growth', False)}")
        print(f"  Combination Logic: {e_sig.get('combination_logic', 'OR')}")

        # Fundamental Signal
        f_sig = config.get('fundamental_signal', {})
        print(f"\n[Fundamental Signal]")
        print(f"  Enabled: {f_sig.get('enabled', False)}")
        print(f"  Market Cap Min: ${f_sig.get('market_cap', {}).get('min', 0):,.0f}")
        print(f"  Market Cap Max: ${f_sig.get('market_cap', {}).get('max', 0):,.0f}")
        print(f"  Revenue YoY Min: {f_sig.get('revenue', {}).get('min_yoy', 0)*100:.1f}%")
        print(f"  Revenue Prev YoY Min: {f_sig.get('revenue', {}).get('min_prev_yoy', 0)*100:.1f}%")
        print(f"  Revenue Min Value: ${f_sig.get('revenue', {}).get('min_value', 0):,.0f}")
        print(f"  EPS YoY Min: {f_sig.get('eps', {}).get('min_yoy', 0)*100:.1f}%")
        print(f"  EPS Prev YoY Min: {f_sig.get('eps', {}).get('min_prev_yoy', 0)*100:.1f}%")
        print(f"  Growth Logic: {f_sig.get('growth_logic', 'OR')}")

        # Weekly Signal
        w_sig = config.get('weekly_signal', {})
        print(f"\n[Weekly Signal]")
        print(f"  Enabled: {w_sig.get('enabled', False)}")
        print(f"  Require 1Y == 2Y High: {w_sig.get('price_levels', {}).get('require_1y_eq_2y_high', False)}")
        print(f"  Require 2Y < 1Y Low: {w_sig.get('price_levels', {}).get('require_2y_lt_1y_low', False)}")
        print(f"  High Stability Factor: {w_sig.get('high_stability', {}).get('factor', 0):.2f}")
        print(f"  High Stability Shift Periods: {w_sig.get('high_stability', {}).get('shift_periods', 0)}")
        print(f"  Low Distance Factor: {w_sig.get('low_distance', {}).get('factor', 0):.2f}")
        print(f"  Low Distance Shift Periods: {w_sig.get('low_distance', {}).get('shift_periods', 0)}")
        print(f"  High Distance Factor: {w_sig.get('high_distance', {}).get('factor', 0):.2f}")
        print(f"  High Distance Shift Periods: {w_sig.get('high_distance', {}).get('shift_periods', 0)}")
        print(f"  Combination Logic: {w_sig.get('combination_logic', 'AND')}")

        # RS Signal
        rs_sig = config.get('rs_signal', {})
        print(f"\n[RS Signal]")
        print(f"  Enabled: {rs_sig.get('enabled', False)}")
        print(f"  Threshold: {rs_sig.get('threshold', 0)}")
        print(f"  Use T-1: {rs_sig.get('use_t_minus_1', False)}")
        print(f"  Use RS 12W: {rs_sig.get('use_rs_12w', False)}")
        print(f"  RS 12W Threshold: {rs_sig.get('rs_12w_threshold', 0)}")
        print(f"  Use Sector RS: {rs_sig.get('use_sector_rs', False)}")
        print(f"  Sector RS Threshold: {rs_sig.get('sector_rs_threshold', 0)}")

        # Daily Signal
        d_sig = config.get('daily_signal', {})
        print(f"\n[Daily Signal]")
        print(f"  Enabled: {d_sig.get('enabled', False)}")
        print(f"  SMA200 Momentum Enabled: {d_sig.get('base_conditions', {}).get('sma200_momentum', {}).get('enabled', False)}")
        print(f"  SMA200 Momentum Allow Zero: {d_sig.get('base_conditions', {}).get('sma200_momentum', {}).get('allow_zero', False)}")
        print(f"  SMA Downtrend Enabled: {d_sig.get('base_conditions', {}).get('sma_downtrend', {}).get('enabled', False)}")
        print(f"  RS Enabled: {d_sig.get('base_conditions', {}).get('rs', {}).get('enabled', False)}")
        print(f"  RS Threshold: {d_sig.get('base_conditions', {}).get('rs', {}).get('threshold', 0)}")
        print(f"  Breakout Enabled: {d_sig.get('breakout', {}).get('enabled', False)}")
        timeframes = d_sig.get('breakout', {}).get('timeframes', [])
        print(f"  Breakout Timeframes: {', '.join(timeframes)}")
        print(f"  Breakout Stop at First: {d_sig.get('breakout', {}).get('stop_at_first', False)}")
        print(f"  Losscut Ratio: {d_sig.get('prices', {}).get('losscut_ratio', 0):.2%}")
        print(f"  Target Multiplier: {d_sig.get('prices', {}).get('target_multiplier', 0):.2f}")
        print(f"  Use T-1: {d_sig.get('use_t_minus_1', False)}")
        print(f"  Default Mode: {d_sig.get('default_mode', 'N/A')}")

        # Thresholds
        thresholds = config.get('thresholds', {})
        print(f"\n[Thresholds]")
        print(f"  E: {thresholds.get('E', 0):.1f}")
        print(f"  F: {thresholds.get('F', 0):.1f}")
        print(f"  W: {thresholds.get('W', 0):.1f}")
        print(f"  RS: {thresholds.get('RS', 0):.1f}")
        print(f"  D: {thresholds.get('D', 0):.1f}")

        print("\n" + "="*80)

    def run(self):
        """CLI 실행"""
        while True:
            self.display_menu()

            try:
                choice = input("\nSelect option: ").strip()

                if choice == "0":
                    print("\nExiting Strategy Manager.")
                    break
                elif choice == "1":
                    self.show_current_strategy()
                elif choice == "2":
                    self.list_strategies()
                elif choice == "3":
                    self.switch_strategy()
                elif choice == "4":
                    self.compare_strategies()
                elif choice == "5":
                    self.show_strategy_details()
                else:
                    print("\n[ERROR] Invalid option. Please try again.")

                input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                print("\n\nExiting Strategy Manager.")
                break
            except Exception as e:
                print(f"\n[ERROR] An error occurred: {e}")
                input("\nPress Enter to continue...")


def main():
    """메인 함수"""
    cli = StrategyManagerCLI()
    cli.run()


if __name__ == "__main__":
    main()
