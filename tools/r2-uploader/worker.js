const SECRET = "steiner-upload-2026";

function auth(request) {
  const token = request.headers.get("X-Auth-Token");
  return token === SECRET;
}

export default {
  async fetch(request, env) {
    if (!auth(request)) {
      return new Response("Unauthorized", { status: 401 });
    }

    const url = new URL(request.url);
    const key = url.searchParams.get("key");
    if (!key) return new Response("Missing ?key=", { status: 400 });

    if (request.method === "POST" && url.pathname === "/create") {
      const mpu = await env.BUCKET.createMultipartUpload(key, {
        httpMetadata: { contentType: "application/pdf" },
      });
      return Response.json({ uploadId: mpu.uploadId });
    }

    if (request.method === "PUT" && url.pathname === "/upload-part") {
      const uploadId = url.searchParams.get("uploadId");
      const partNumber = parseInt(url.searchParams.get("partNumber"));
      if (!uploadId || !partNumber) {
        return new Response("Missing uploadId or partNumber", { status: 400 });
      }
      const mpu = env.BUCKET.resumeMultipartUpload(key, uploadId);
      const part = await mpu.uploadPart(partNumber, request.body);
      return Response.json({ partNumber: part.partNumber, etag: part.etag });
    }

    if (request.method === "POST" && url.pathname === "/complete") {
      const uploadId = url.searchParams.get("uploadId");
      if (!uploadId) return new Response("Missing uploadId", { status: 400 });
      const { parts } = await request.json();
      const mpu = env.BUCKET.resumeMultipartUpload(key, uploadId);
      await mpu.complete(parts);
      return Response.json({ success: true, key });
    }

    if (request.method === "DELETE" && url.pathname === "/abort") {
      const uploadId = url.searchParams.get("uploadId");
      if (!uploadId) return new Response("Missing uploadId", { status: 400 });
      const mpu = env.BUCKET.resumeMultipartUpload(key, uploadId);
      await mpu.abort();
      return Response.json({ aborted: true });
    }

    return new Response("Not found", { status: 404 });
  },
};
