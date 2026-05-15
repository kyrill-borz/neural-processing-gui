# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, copy_metadata, collect_dynamic_libs
datas = [('style.css', '.')]
binaries = []
hiddenimports = ['PyQt5.sip']
tmp_ret = collect_all('PyQt5')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('numpy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('scipy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pandas')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('matplotlib')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('polars')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pyarrow')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
hiddenimports += ['pyarrow','dask','dask.array', 'dask.dataframe', 'dask.bag', 'dask.delayed', 'numpy.core', 'numpy.linalg', 'numpy.fft', 'numpy.core.multiarray', 'pkg_resources', 'numpy.core._methods','numpy.linalg.lapack_lite']

datas += copy_metadata('numpy')
datas += copy_metadata('pandas')
datas += copy_metadata('dask')
datas += copy_metadata('scipy')
datas += copy_metadata('pyarrow')

binaries += collect_dynamic_libs('numpy')
binaries += collect_dynamic_libs('scipy')
binaries += collect_dynamic_libs('pyarrow')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[ 'rthook_dll.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name='NeuralGui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='NeuralGui'
)
