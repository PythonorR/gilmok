// Placeholder landing page for Step 1. The dashboard and map are built in Step 3.
export default function Home() {
  return (
    <main className="flex flex-1 items-center justify-center bg-slate-50 p-6">
      <div className="max-w-md rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
        <p className="text-sm font-medium text-emerald-600">길목</p>
        <h1 className="mt-2 text-2xl font-bold text-slate-900">상권 입지 분석</h1>
        <p className="mt-3 leading-relaxed text-slate-600">
          대시보드와 지도는 준비 중입니다. 첫 버전은 서울 마포구의 카페 업종을 지원합니다.
        </p>
      </div>
    </main>
  );
}
