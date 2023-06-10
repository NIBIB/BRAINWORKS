import {
  Button,
  ButtonGroup,
  Card,
  CardBody,
  CardFooter,
  Divider,
  Heading,
  Stack,
  Text,
  Tooltip,
  useDisclosure,
} from "@chakra-ui/react";
import SkeletonImage from "common/components/SkeletonImage";
import { useNavigate } from "react-router-dom";

import VisualizerInfoModal from "../../../components/VisualizerInfoModal";
import { VisualizerSelectionType } from "../../../models";

/**
 * VisualizerSelectCard
 *
 * React component that renders a card with image, title, desc, when clicked brings to the corresponding tool page
 */
const VisualizerSelectCard = ({
  title,
  desc,
  img,
  route,
}: VisualizerSelectionType) => {
  const navigate = useNavigate();
  const { onOpen, isOpen, onClose } = useDisclosure();

  const handleSelectVisualizer = () => {
    navigate(`/visualizers/form/${route}`);
  };

  return (
    <>
      <VisualizerInfoModal
        representation={route}
        isOpen={isOpen}
        onClose={onClose}
      />
      <Card maxW="sm" bg="white">
        <CardBody>
          <SkeletonImage
            objectFit="cover"
            src={`${process.env.PUBLIC_URL}/images/${img}`}
            alt={title}
            borderRadius="lg"
            border="1px"
            h="200px"
            w="100%"
            borderColor="gray.200"
          />
          <Stack mt="6" spacing="3">
            <Heading size="md">{title}</Heading>
            <Text>{desc}</Text>
          </Stack>
        </CardBody>
        <Divider />
        <CardFooter>
          <ButtonGroup spacing="2">
            <Button
              variant="solid"
              colorScheme="blue"
              onClick={handleSelectVisualizer}
            >
              Select
            </Button>

            <Tooltip
              color="white"
              hasArrow
              label={`Click to view infomation about ${title}`}
              aria-label={`Tooltip to with an informational preview about ${title}`}
            >
              <Button variant="ghost" colorScheme="blue" onClick={onOpen}>
                Preview
              </Button>
            </Tooltip>
          </ButtonGroup>
        </CardFooter>
      </Card>
    </>
  );
};

export default VisualizerSelectCard;
