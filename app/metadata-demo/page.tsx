import { MetadataViewer } from '@/components/metadata-viewer';

export default function MetadataDemoPage() {
  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">AI Image Metadata Viewer</h1>
        <p className="text-gray-600 mb-8">
          Upload an AI-generated image to extract generation parameters
        </p>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <MetadataViewer />
        </div>

        <div className="mt-8 space-y-4 text-sm text-gray-600">
          <h2 className="text-lg font-semibold text-gray-900">Supported Formats:</h2>
          <ul className="list-disc list-inside space-y-2">
            <li>
              <strong>PNG:</strong> A1111/Automatic1111, ComfyUI, NovelAI
            </li>
            <li>
              <strong>JPEG:</strong> Civitai images (A1111 and ComfyUI formats stored in EXIF)
            </li>
          </ul>

          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-blue-900 font-medium">Note:</p>
            <p className="text-blue-800 text-sm mt-1">
              Most social media platforms strip metadata from images when you upload them.
              Download the original file directly from the generation tool for best results.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
