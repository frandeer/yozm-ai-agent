#!/bin/bash

# chapter1 디렉토리의 모든 파이썬 스크립트를 실행합니다.

echo "Running chapter1 scripts..."

# chapter1 디렉토리로 이동
cd chapter1

# 디렉토리 내의 모든 .py 파일을 순회하며 실행
for file in *.py
do
  echo "----------------------------------------"
  echo "Executing $file..."
  echo "----------------------------------------"
  python "$file"
  echo -e "\n"
done

echo "All chapter1 scripts have been executed."
