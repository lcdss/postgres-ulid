#!/bin/sh
set -eu

pg_config_path="${1:?pg_config path is required}"

if [ "$#" -eq 2 ]; then
  source_root=
  output_root="${2:?output root is required}"
else
  source_root="${2:?source root is required}"
  output_root="${3:?output root is required}"
fi

pkglibdir="$("${pg_config_path}" --pkglibdir)"
extension_dir="$("${pg_config_path}" --sharedir)/extension"

install -d "${output_root}${pkglibdir}" "${output_root}${extension_dir}"
cp "${source_root}${pkglibdir}"/*ulid*.so "${output_root}${pkglibdir}/"
cp "${source_root}${extension_dir}"/*ulid* "${output_root}${extension_dir}/"
