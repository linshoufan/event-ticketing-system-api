import { motion } from "framer-motion"

interface Props {
  children: React.ReactNode
}

// src/components/PageTransition.tsx
function PageTransition({ children }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  )
}

export default PageTransition