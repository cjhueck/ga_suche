export default {
  async fetch(request, env) {
    if (request.method === 'PUT') {
      const url = new URL(request.url);
      const key = url.pathname.replace(/^\/r2upload\//, '');
      if (!key) return new Response('Key required', { status: 400 });

      await env.BUCKET.put(key, request.body, {
        httpMetadata: { contentType: 'application/pdf' }
      });

      return new Response(`Uploaded: ${key}`, { status: 200 });
    }
    return new Response('PUT /r2upload/{key} to upload', { status: 405 });
  }
};
