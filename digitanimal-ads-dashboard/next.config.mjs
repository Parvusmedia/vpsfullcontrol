/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  distDir: "dist",
  serverExternalPackages: ["pg"],
};

export default nextConfig;
