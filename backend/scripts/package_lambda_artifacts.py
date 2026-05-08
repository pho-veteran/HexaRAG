import os
import shutil
import sysconfig
import zipfile
from pathlib import Path

from hexarag_api.services.lambda_packaging import build_artifact_specs


def _copy_dependency_matches(site_packages: Path, staging_root: Path, patterns: tuple[str, ...]) -> None:
    copied: set[Path] = set()
    for pattern in patterns:
        for match in site_packages.glob(pattern):
            if match in copied or not match.exists():
                continue
            destination = staging_root / match.name
            if match.is_dir():
                shutil.copytree(match, destination, dirs_exist_ok=True)
            else:
                shutil.copy2(match, destination)
            copied.add(match)


def _write_zip(staging_root: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(staging_root.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(staging_root))


def package_artifacts() -> list[Path]:
    repo_root = Path(os.environ.get('HEXARAG_REPO_ROOT', '/workspace/repo')).resolve()
    site_packages = Path(sysconfig.get_paths()['purelib'])
    build_root = repo_root / '.lambda-build'
    specs = build_artifact_specs(repo_root)
    outputs: list[Path] = []

    if build_root.exists():
        shutil.rmtree(build_root)
    build_root.mkdir(parents=True, exist_ok=True)

    for spec in specs.values():
        staging_root = build_root / spec.name
        staging_root.mkdir(parents=True, exist_ok=True)

        for package_dir in spec.package_dirs:
            shutil.copytree(package_dir, staging_root / package_dir.name, dirs_exist_ok=True)
        for root_file in spec.root_files:
            shutil.copy2(root_file, staging_root / root_file.name)
        _copy_dependency_matches(site_packages, staging_root, spec.dependency_globs)
        _write_zip(staging_root, spec.output_path)
        outputs.append(spec.output_path)

    return outputs


if __name__ == '__main__':
    for output in package_artifacts():
        print(output)
