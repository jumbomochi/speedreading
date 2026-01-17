import { useCallback, useState } from 'react';

interface Props {
  onFileSelect: (file: File) => void;
  isUploading: boolean;
  acceptedTypes: string;
}

export function FileUpload({ onFileSelect, isUploading, acceptedTypes }: Props) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const file = e.dataTransfer.files[0];
      if (file) {
        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileSelect(file);
    }
  };

  return (
    <div
      className={`file-upload ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      {isUploading ? (
        <div className="upload-spinner">
          <div className="spinner"></div>
          <span>Uploading...</span>
        </div>
      ) : (
        <>
          <div className="upload-icon">📄</div>
          <p>Drag and drop a file here, or click to select</p>
          <p className="file-types">Supported: PDF, EPUB, TXT</p>
          <input
            type="file"
            accept={acceptedTypes}
            onChange={handleFileInput}
            className="file-input"
          />
        </>
      )}
    </div>
  );
}
