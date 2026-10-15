"""Export item QR identifiers from the running API to a CSV manifest.
Usage: python scripts/export_qr_manifest.py --url http://127.0.0.1:8000 --output qr_manifest.csv
"""
import argparse, csv, sys
from urllib.error import URLError
from urllib.request import urlopen
import json

def main():
    parser=argparse.ArgumentParser(description="Export inventory QR manifest")
    parser.add_argument('--url',default='http://127.0.0.1:8000',help='API base URL')
    parser.add_argument('--output',default='qr_manifest.csv')
    args=parser.parse_args()
    try:
        with urlopen(args.url.rstrip('/')+'/api/items',timeout=10) as response:
            items=json.loads(response.read().decode('utf-8'))
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f'Could not retrieve items from API: {exc}',file=sys.stderr); return 1
    with open(args.output,'w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['item_id','name','category','qr_code','quantity_total','quantity_available'])
        writer.writeheader()
        for item in items:
            writer.writerow({key:item.get(key,'') for key in writer.fieldnames})
    print(f'Exported {len(items)} item(s) to {args.output}')
    return 0
if __name__=='__main__': raise SystemExit(main())
