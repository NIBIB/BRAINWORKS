import { Image, ImageProps, Skeleton } from "@chakra-ui/react";
import { useState } from "react";

/**
 * SkeletonImage
 *
 * React component that renders a skeleton placeholder when loading the image
 */
const SkeletonImage = (props: ImageProps) => {
  const [load, setLoad] = useState(false);

  const onImageLoad = () => {
    setLoad(true);
  };

  return (
    <Skeleton isLoaded={load} w="100%">
      <Image onLoad={onImageLoad} {...props} />
    </Skeleton>
  );
};

export default SkeletonImage;
