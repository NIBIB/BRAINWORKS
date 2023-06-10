import {
  Button,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
} from "@chakra-ui/react";
import { findVisualizerInfo } from "../../utils";
import PaperCitationsInfoModal from "./visualizers/PaperCitationsInfoModal";
import PaperTriplesInfoModal from "./visualizers/PaperTriplesInfoModal";
import TopicCoOccurrencesInfoModal from "./visualizers/TopicCoOccurrencesInfoModal";
import TriplesInfoModal from "./visualizers/TriplesInfoModal";

// * Diciontary determines which modal is rendered
const MODAL_DICT: any = {
  paper_triples: <PaperTriplesInfoModal />,
  topic_co_occurrences: <TopicCoOccurrencesInfoModal />,
  paper_citations: <PaperCitationsInfoModal />,
  triples: <TriplesInfoModal />,
};

interface AppProps {
  representation: string;
  isOpen: boolean;
  onClose: () => void;
}

const VisualizerInfoModal = ({ representation, isOpen, onClose }: AppProps) => {
  const visualizerInfo = findVisualizerInfo(representation);

  return (
    <Modal isCentered isOpen={isOpen} onClose={onClose}>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>{visualizerInfo?.title} Infomation</ModalHeader>
        <ModalCloseButton />
        <ModalBody px={10}>{MODAL_DICT[representation]}</ModalBody>
        <ModalFooter>
          <Button colorScheme="blue" mr={3} onClick={onClose}>
            Close
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default VisualizerInfoModal;
