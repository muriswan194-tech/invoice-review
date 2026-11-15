import { useRef, useState } from 'react'

type Props = { selectedFile: File | null; onFile: (file: File) => void; onClear: () => void }
const ACCEPTED = ['application/pdf', 'image/png', 'image/jpeg']
const MAX_BYTES = 4 * 1024 * 1024

function UploadStep({ selectedFile, onFile, onClear }: Props) {
  const fileInput = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [fileError, setFileError] = useState<string | null>(null)
  function chooseFile(file: File | undefined) {
    if (!file) return
    if (!ACCEPTED.includes(file.type)) { setFileError('Choose a PDF, PNG, or JPEG file.'); return }
    if (file.size > MAX_BYTES) { setFileError('Files must be 4 MB or smaller.'); return }
    setFileError(null); onFile(file)
  }
  return <div className="upload-step">
    <div className={`upload-dropzone ${isDragging ? 'is-dragging' : ''}`.trim()} onDragOver={(event) => { event.preventDefault(); setIsDragging(true) }} onDragLeave={() => setIsDragging(false)} onDrop={(event) => { event.preventDefault(); setIsDragging(false); chooseFile(event.dataTransfer.files?.[0]) }}>
      <svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 16V5m0 0L8 9m4-4 4 4M5 15v2a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg><strong>Drop a GST invoice here</strong><p>or click to browse · PDF or image · maximum 4 MB</p><button type="button" className="dropzone-button" onClick={() => fileInput.current?.click()}>Choose a file</button>
    </div>
    <input ref={fileInput} type="file" accept=".pdf,.png,.jpg,.jpeg" hidden onChange={(event) => { chooseFile(event.target.files?.[0]); event.target.value = '' }} />
    {fileError && <p className="input-error">{fileError}</p>}
    {selectedFile && <div className="selected-file"><div><strong>{selectedFile.name}</strong><span>{(selectedFile.size / 1024 / 1024).toFixed(2)} MB · {selectedFile.type === 'application/pdf' ? 'PDF' : 'Image'}</span></div><button type="button" className="button-secondary button-small" onClick={onClear}>Remove</button></div>}
  </div>
}

export default UploadStep
