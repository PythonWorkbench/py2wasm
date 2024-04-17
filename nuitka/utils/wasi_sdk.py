import os
import platform
import shutil
import subprocess
import sys
import tarfile

# import appdirs
import requests
import tqdm


# sdk_dir = os.path.join(appdirs.user_data_dir("wasi-sdk", "py2wasm"))
sdk_dir = wasi_python_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wasi-sdk/21")


def download_sdk(before=None):
    try:
        os.makedirs(sdk_dir)

    except FileExistsError:
        pass

    url = "https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-21/"
    if platform.system() == "Windows":
        file = "wasi-sdk-21.0.m-mingw.tar.gz"

    elif platform.system() == "Linux":
        file = "wasi-sdk-21.0-linux.tar.gz"

    elif platform.system() == "Darwin":
        file = "wasi-sdk-21.0-macos.tar.gz"

    else:
        raise Exception(f"Platform {platform.system()} not supported")

    url += file
    if not os.path.exists(os.path.join(sdk_dir, file)):
        print(f"Downloading {file}")
        with requests.get(url, stream=True) as req:
            req.raise_for_status()

            with open(os.path.join(sdk_dir, file), "wb+") as fp, tqdm.tqdm(
                desc=file,
                total=int(req.headers.get("content-length", 0)),
                unit="MiB",
                unit_scale=True,
                unit_divisor=1024,
            ) as progress:
                for chunk in req.iter_content(4096):
                    progress.update(fp.write(chunk))

    print(f"Extracting {file}")
    with tarfile.open(os.path.join(sdk_dir, file)) as tar:
        extracted = tar.getnames()[0]
        tar.extractall(sdk_dir)

    shutil.move(
        os.path.join(sdk_dir, extracted),
        os.path.join(sdk_dir, f"sdk-{platform.system()}"),
    )

    print(f"wasi-sdk installed at: {os.path.join(sdk_dir, 'sdk')}")
    if before is not None:
        before()

WASI_SDK_BASE_PATH = f"{sdk_dir}/sdk-{platform.system()}"


def try_get_sdk_path():
    WASI_SDK_DIR_ENV = os.environ.get("WASI_SDK_DIR")
    if WASI_SDK_DIR_ENV:
        print("Using WASI_SDK_DIR environment variable")
        wasi_sdk = WASI_SDK_DIR_ENV
    else:
        wasi_sdk = WASI_SDK_BASE_PATH

    clang_path = f"{wasi_sdk}/bin/clang"
    sysroot_path = f"{wasi_sdk}/share/wasi-sysroot"
    if not os.path.isdir(wasi_sdk):
        print(f"wasi-sdk not found in {wasi_sdk}, downloading the SDK")
        download_sdk()
        return WASI_SDK_BASE_PATH
    else:
        print(f"Using WASI_SDK from {wasi_sdk}")
        if not os.path.exists(clang_path):
            print(f"Clang doesn't exist in the path: {clang_path}")
            return False
        if not os.path.isdir(sysroot_path):
            print(f"The WASI Sysroot {clang_path} doesn't exist")
            return False
        return wasi_sdk
