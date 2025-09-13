#!/usr/bin/env python3
"""下载 XYZ 瓦片到 assets/tiles/ 的脚本。

用法示例：
  python download_tiles.py --min-zoom 12 --max-zoom 14 --bbox 121.0,31.0,121.6,31.6

参数说明：
- bbox 格式为 lon_min,lat_min,lon_max,lat_max（十进制度），注意经度在前。
- 默认使用 tile.openstreetmap.org 模板（请遵守其使用条款）；可用 --template 指定其它瓦片服务器模板。

输出：将 PNG 文件保存为 assets/tiles/{z}/{x}/{y}.png
"""
import argparse
import math
import os
import time
from pathlib import Path

import requests


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return xtile, ytile


def clamp(v, a, b):
    return max(a, min(b, v))


def download_tile(session, url, dest_path, headers=None, delay=0.1):
    if dest_path.exists():
        return True
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        resp = session.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            with open(dest_path, 'wb') as f:
                f.write(resp.content)
            time.sleep(delay)
            return True
        else:
            return False
    except Exception:
        return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--min-zoom', type=int, required=True)
    p.add_argument('--max-zoom', type=int, required=True)
    p.add_argument('--bbox', type=str, required=True,
                   help='lon_min,lat_min,lon_max,lat_max')
    p.add_argument('--template', type=str, default='https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                   help='tile URL template with {z}/{x}/{y}')
    p.add_argument('--output', type=str, default='./assets/tiles', help='output tiles folder')
    p.add_argument('--delay', type=float, default=0.1, help='delay between requests (s)')
    args = p.parse_args()

    lon_min, lat_min, lon_max, lat_max = [float(x) for x in args.bbox.split(',')]
    output = Path(args.output)
    session = requests.Session()
    session.headers.update({'User-Agent': 'GeoReconViewerTileDownloader/1.0 (+https://example)'})

    # Warn about using public servers
    if 'tile.openstreetmap.org' in args.template:
        print('注意：你正在使用 tile.openstreetmap.org 作为数据源。大规模下载会违反 OSM 的使用条款，请自行搭建 tileserver 或使用授权服务。')

    for z in range(args.min_zoom, args.max_zoom + 1):
        # compute tile range
        x0, y1 = deg2num(lat_min, lon_min, z)
        x1, y0 = deg2num(lat_max, lon_max, z)
        # normalize ranges
        x_min = min(x0, x1)
        x_max = max(x0, x1)
        y_min = min(y0, y1)
        y_max = max(y0, y1)
        max_tile = 2 ** z - 1
        x_min = clamp(x_min, 0, max_tile)
        x_max = clamp(x_max, 0, max_tile)
        y_min = clamp(y_min, 0, max_tile)
        y_max = clamp(y_max, 0, max_tile)

        print(f'Downloading zoom {z} tiles: x {x_min}..{x_max}, y {y_min}..{y_max}')

        downloaded_any = False
        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                url = args.template.format(z=z, x=x, y=y)
                dest = output / str(z) / str(x) / f"{y}.png"
                ok = download_tile(session, url, dest, delay=args.delay)
                if ok:
                    downloaded_any = True
                else:
                    print(f'Failed: {url}')

        # If any tile downloaded in this zoom level, create a marker file so frontend can detect tiles
        if downloaded_any:
            marker = output / '.tiles_present'
            try:
                marker.parent.mkdir(parents=True, exist_ok=True)
                marker.write_text('ok')
            except Exception:
                pass

    # Write metadata (bbox, zoom range, suggested center and zoom)
    try:
        meta = {
            'bbox': [lon_min, lat_min, lon_max, lat_max],
            'min_zoom': args.min_zoom,
            'max_zoom': args.max_zoom,
        }
        # compute center
        meta['center'] = [(lat_min + lat_max) / 2.0, (lon_min + lon_max) / 2.0]
        meta['suggested_zoom'] = args.max_zoom
        (output / 'metadata.json').write_text(__import__('json').dumps(meta))
    except Exception:
        pass


if __name__ == '__main__':
    main()
