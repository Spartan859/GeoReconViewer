# GeoReconViewer

示例 PySide6 应用，用于演示：左侧加载/浏览三维重建结果（.obj 占位），右侧嵌入离线地图（Leaflet），并用 QtWebChannel 建立 Python↔JS 通信。

快速开始
1. 创建并激活 Python 虚拟环境（Windows PowerShell）

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. 运行应用

```powershell
python main.py
```

说明
- `main.py` - PySide6 主程序。
- `assets/map.html` - 嵌入的本地 Leaflet 地图示例，使用 QtWebChannel 与 Python 交互。

后续
- 加入真正的 3D 渲染（OpenGL / pyqtgraph / trimesh + vispy），OBJ 加载与拾取。
- 实现 3D 点到经纬度的映射（需要重建的 georeference 元数据）。

离线地图准备（使用 `download_tiles.py`）
----------------
本仓库提供了 `download_tiles.py` 脚本，用于把 XYZ 瓦片下载到 `assets/tiles/{z}/{x}/{y}.png`，并为前端生成简单的 `metadata.json`，方便 `assets/map.html` 检测到本地瓦片并使用它们。

重要：默认模板指向 `https://tile.openstreetmap.org/{z}/{x}/{y}.png`。请遵守数据源的使用条款——不要对公共服务器进行大规模无授权下载。建议对小范围区域和小的缩放级别进行测试，或使用经授权的 tileserver。

用法示例（PowerShell）：

```powershell
# 在项目根目录下运行：下载 12-13 级别、覆盖一个小 bbox（经度在前）
python download_tiles.py --min-zoom 12 --max-zoom 13 --bbox 121.0,31.0,121.6,31.6
```

可选参数说明：
- `--min-zoom` / `--max-zoom`：缩放级别范围（整数）。
- `--bbox`：经度/纬度边界，格式 `lon_min,lat_min,lon_max,lat_max`（十进制度）。注意经度在前。
- `--template`：瓦片模板（带 `{z}` `{x}` `{y}`），默认 `https://tile.openstreetmap.org/{z}/{x}/{y}.png`。
- `--output`：输出目录，默认 `./assets/tiles`。
- `--delay`：请求间隔（秒），默认为 `0.1`，可增大以减轻目标服务器压力。

运行后产物：
- 脚本会写入 `assets/tiles/metadata.json`，包含 `bbox`、`min_zoom`、`max_zoom`、`center` 与 `suggested_zoom`，供 `assets/map.html` 用于初始定位。

验证步骤：
1. 运行上述 `download_tiles.py` 命令（建议先用小 bbox 和窄缩放级别进行试验）。
2. 确认 `assets/tiles/metadata.json` 已创建。
3. 启动应用：

```powershell
python main.py
```

4. 在应用中打开 Map 窗口（或直接用浏览器打开 `assets/map.html`），确认地图瓦片加载正常且不再请求外部网络（观察控制台或网络面板）。

故障排查提示：
- 如果浏览器或 `QWebEngineView` 控制台仍提示外部请求或 `ERR_NETWORK_ACCESS_DENIED`，请检查 `main.py` 中是否为 `QWebEngineView` 设置了允许本地内容访问文件/远程资源的选项（`LocalContentCanAccessFileUrls`/`LocalContentCanAccessRemoteUrls`）。
- 如果图标（marker）丢失，确保 `assets/leaflet/images` 中包含 Leaflet 的 `marker-icon.png`、`marker-icon-2x.png`、`marker-shadow.png`，或在 `assets/map.html` 中采用内联 data-URI 图标。

示例：只为小范围下载并验证的推荐命令：
```powershell
python download_tiles.py --min-zoom 12 --max-zoom 13 --bbox 121.1,31.1,121.2,31.2 --delay 0.2
```
