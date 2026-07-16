export async function getFileSize(url) {
    try {
      const response = await fetch(url, { method: 'HEAD' });
      if (response.ok) {
        const size = response.headers.get('Content-Length');
        if (size) {
          console.log(`File size: ${size} bytes`);
          return formatBytes(size);
        } else {
          console.log('Content-Length header not found');
          return null;
        }
      } else {
        console.error('Failed to fetch file headers:', response.statusText);
        return null;
      }
    } catch (error) {
      console.error('Error fetching file headers:', error);
      return null;
    }
  }
  

  function formatBytes(bytes) {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + ' ' + sizes[i];
  }