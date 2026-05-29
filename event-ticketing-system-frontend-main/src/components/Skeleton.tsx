function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse bg-zinc-800 rounded-xl ${className}`}
    />
  )
}

export function EventCardSkeleton() {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
      <div className="flex items-start gap-4">
        <Skeleton className="w-12 h-12 rounded-xl flex-shrink-0" />
        <div className="flex-1">
          <Skeleton className="h-5 w-48 mb-2" />
          <Skeleton className="h-4 w-32 mb-1" />
          <Skeleton className="h-4 w-40" />
        </div>
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
    </div>
  )
}

export function TicketCardSkeleton() {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
      <div className="flex items-start gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Skeleton className="w-2 h-2 rounded-full" />
            <Skeleton className="h-5 w-40" />
          </div>
          <Skeleton className="h-4 w-32 mb-1" />
          <Skeleton className="h-4 w-36" />
        </div>
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
    </div>
  )
}

export function TransactionCardSkeleton() {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Skeleton className="w-2 h-2 rounded-full" />
          <Skeleton className="h-5 w-36" />
        </div>
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
      <Skeleton className="h-4 w-48 mb-3" />
      <div className="flex gap-4 mb-4">
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-16" />
      </div>
    </div>
  )
}

export default Skeleton

export function EventRowSkeleton() {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 flex items-center gap-4">
      <div className="flex-1">
        <Skeleton className="h-5 w-48 mb-2" />
        <div className="flex gap-2">
          <Skeleton className="h-4 w-16 rounded-full" />
          <Skeleton className="h-4 w-24" />
        </div>
      </div>
      <div className="flex gap-2">
        <Skeleton className="h-7 w-16 rounded-lg" />
        <Skeleton className="h-7 w-16 rounded-lg" />
        <Skeleton className="h-7 w-16 rounded-lg" />
      </div>
    </div>
  )
}

export function UserRowSkeleton() {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 flex items-center gap-4">
      <Skeleton className="w-10 h-10 rounded-xl flex-shrink-0" />
      <div className="flex-1">
        <Skeleton className="h-5 w-32 mb-1" />
      </div>
      <Skeleton className="h-8 w-24 rounded-lg" />
      <Skeleton className="h-6 w-16 rounded-full" />
      <Skeleton className="h-7 w-12 rounded-lg" />
    </div>
  )
}

export function StatCardSkeleton() {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-7 w-16 rounded-lg" />
      </div>
      <div className="grid grid-cols-4 gap-4 mb-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i}>
            <Skeleton className="h-3 w-8 mb-1" />
            <Skeleton className="h-7 w-12" />
          </div>
        ))}
      </div>
      <Skeleton className="h-1.5 w-full rounded-full mb-2" />
      <Skeleton className="h-1.5 w-full rounded-full" />
    </div>
  )
}