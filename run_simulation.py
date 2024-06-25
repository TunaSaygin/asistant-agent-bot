import argparse
import tqdm
from loaders import load_mwoz
import Dialog.utils
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database_path", type=str, default="multiwoz_database")
    parser.add_argument("--dataset", type=str, default="multiwoz")
    parser.add_argument("--split", type=str, default='test')
    parser.add_argument("--single_domain", action='store_true')
    parser.add_argument("--restrict_domains", type=str)
    parser.add_argument("--dials_total", type=int, default=5)
    args = parser.parse_args()
    total = args.dials_total
    last_dial_id = None
    data_gen = \
                load_mwoz(args.database_path, args.context_size, split=args.split, total=total, shuffle=False, only_single_domain=args.single_domain, restrict_domains=args.restrict_domains.split(",") if args.restrict_domains is not None else None)

    tn = 0
    progress_bar = tqdm.tqdm(total=total)
    for it, turn in enumerate(data_gen):
        if last_dial_id != turn['dialogue_id']:
            last_dial_id = turn['dialogue_id']
            n += 1
            progress_bar.update(1)
            tn = 0
            if n > total:
                break