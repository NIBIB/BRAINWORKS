import { useEffect } from "react";

/**
 * usePageTitle
 *
 * React hook that changes the document title to the given `string` | BRAINWORKS
 */
const usePageTitle = (title: string) => {
  useEffect(() => {
    document.title = `${title} | BRAINWORKS`;
  }, [title]);

  return null;
};

export default usePageTitle;
