"""Entry point: python main.py"""

import logging
from datetime import date

from dhms_export.config import load_config
from dhms_export.db import get_engine, read_table
from dhms_export.writer import get_output_dirs, to_bytes, write_bytes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("dhms_export")


def main() -> None:
    cfg = load_config()
    engine = get_engine(cfg)
    dated_dir, latest_dir = get_output_dirs(cfg.output_dir, date.today())
    log.info("Writing to %s and %s", dated_dir, latest_dir)

    failed = []
    for table in cfg.tables:
        try:
            df = read_table(engine, table, cfg.db_schema)
            data = to_bytes(df, cfg.output_format)  # serialize once, write twice
            write_bytes(data, dated_dir, table, cfg.output_format)
            write_bytes(data, latest_dir, table, cfg.output_format)
            log.info("%-35s %8d rows", table, len(df))
        except Exception as e:
            log.error("%-35s FAILED: %s", table, e)
            failed.append(table)

    engine.dispose()

    log.info("Exported %d/%d tables", len(cfg.tables) - len(failed), len(cfg.tables))
    if failed:
        raise SystemExit(f"Export failed for: {', '.join(failed)}")


if __name__ == "__main__":
    main()
