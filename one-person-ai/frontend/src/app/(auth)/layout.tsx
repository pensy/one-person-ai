// auth 页面(login/register)不需要主导航,只居中
export default function AuthGroupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-md px-6">{children}</div>
    </div>
  );
}
