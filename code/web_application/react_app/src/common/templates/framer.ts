import { Variants } from "framer-motion";
/**
 * Fade in children variants
 */

// Wrapper variant
export const fadeInChildrenWrapper: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,
    },
  },
};

// Item being faded variant
export const fadeInChildrenItem: Variants = {
  hidden: { opacity: 0, y: "3%" },
  show: {
    opacity: 1,
    y: "0%",
    transition: {
      ease: "easeInOut",
      duration: 0.5,
    },
  },
};
