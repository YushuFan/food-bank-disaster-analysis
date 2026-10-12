"""Reproduce all published analysis and report outputs from bundled aggregates."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from foodbank.analyze import analyze
from foodbank.present import present

if __name__=='__main__':
    analyze(ROOT/'data/public',ROOT/'reports')
    present(ROOT/'data/public',ROOT/'reports')
