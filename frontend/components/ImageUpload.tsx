"use client";

import { ChangeEvent, DragEvent, useEffect, useState } from "react";

interface ImageUploadProps {
  disabled: boolean;
  onSelect: (file: File | null) => void;
}

export default function ImageUpload({ disabled, onSelect }: ImageUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  useEffect(() => {
    if (!file) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  function select(nextFile: File | null) {
    setFile(nextFile);
    onSelect(nextFile);
  }

  function onDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    if (!disabled) select(event.dataTransfer.files[0] ?? null);
  }

  function onChange(event: ChangeEvent<HTMLInputElement>) {
    select(event.target.files?.[0] ?? null);
  }

  return (
    <label
      className={`flex min-h-24 cursor-pointer items-center gap-4 rounded-2xl border border-dashed border-ink/20 bg-white/70 p-4 transition hover:border-moss ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
      onDragOver={(event) => event.preventDefault()}
      onDrop={onDrop}
    >
      {preview ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={preview} alt="Selected image preview" className="h-16 w-16 rounded-xl object-cover" />
      ) : (
        <span className="grid h-16 w-16 place-items-center rounded-xl bg-cream text-2xl" aria-hidden="true">
          ↥
        </span>
      )}
      <span className="min-w-0 flex-1">
        <span className="block font-medium">{file ? file.name : "Search with an image"}</span>
        <span className="mt-1 block text-sm text-ink/60">Drop an image here or browse · JPEG, PNG, WebP</span>
      </span>
      <input
        className="sr-only"
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={onChange}
        disabled={disabled}
        aria-label="Choose an image to search"
      />
    </label>
  );
}
