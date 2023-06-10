import {
  Heading,
  ListItem,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  Text,
  UnorderedList,
  VStack,
} from "@chakra-ui/react";

import { gray300 } from "../../../../../setup/theme/colors";

const TOS_BULLETS = [
  "You must be at least 18 years of age to register an account.",
  "You must allow us to contact you via email to request feedback about our service.",
  "We are not responsible for any misinformation that may be encountered during use of this website. All data is pulled from existing publications without any guarantee of validity.",
  "You may not use the information obtained for commercial gain",
  "You may not attempt to harvest data from our service by means other than what we provide.",
  "We reserve the right to terminate your account at any time if your activity is deemed to be in violation of these terms.",
];

const DATA_POLICY = [
  {
    heading: "Personal Information",
    desc: "We collect all personal information that you voluntarily provide to us upon registration, including your name and email address. This information will not be shared with anyone and is securely protected. In the unlikely event of a data breach, we will promptly notify you if we determine that your data has been compromised. We also ask for information pertaining to your affiliated company or institution, including its name, country of operation, and your department and position within it. This information will be used to identify general usage trends of your institution. We may use this information to contact you for feedback. With your consent, we may also ask to post a testimonial regarding your use of our service.",
  },
  {
    heading: "Data Collection",
    desc: "Some information will be automatically collected upon vising our website, such as your Internet Protocol (IP) address and your device/browser characteristics. While viewing out site, we also record the date and time of access, pages viewed, searches made, and actions taken within the scope of our service. This information does not reveal your identity and is needed to maintain the security and operation of our website, as well as for internal analytics. We also collect information through the use of cookies, which is necessary for the function of our service. If you choose to block the use of cookies for our website, you may not be able to use some portions of our service. We may use this data for analytic purposes such as data analysis, identifying usage trends, tracking user engagement, and monitoring traffic to our website. This data is stored in an aggregated and anonymous form such that individuals cannot be identified.",
  },
  {
    heading: "Children's Privacy",
    desc: "We do not knowingly collect personal information from children under the age of 18. If we learn that the personal information of an individual under 18 has been provided, we will deactivate the account and remove all associated information from our records. If you are a parent or guardian and you are aware that your child has provided us with personal information, please contact us so that we may take action.",
  },
  {
    heading: "Future changes to this policy",
    desc: "We may update our Privacy Policy from time to time. Thus, we advise you to review this page periodically for any changes. These changes are effective immediately when posted on our website. If you have questions or feedback about our data policy, do not hesitate to contact us.",
  },
];

interface AppProps {
  /**
   * `function` - ChakraUI close modal callback
   */
  onClose: () => void;
  /**
   * `boolean` - ChakraUI's modal boolean to determine if the modal should be shown
   */
  isOpen: boolean;
}

/**
 * TermsOfService
 *
 * React component that renders a centered modal displaying all the terms of service
 */
const TermsOfService = ({ onClose, isOpen }: AppProps) => {
  return (
    <>
      <Modal onClose={onClose} isOpen={isOpen} isCentered>
        <ModalOverlay />
        <ModalContent h="500px">
          <ModalHeader borderBottom={`1px solid ${gray300}`}>
            Terms and conditions
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody h={300} overflowY="scroll">
            <VStack spacing={5} py={5}>
              {/* Map TOS Bullets */}
              <VStack align="flex-start">
                <Heading size="md">Terms of service</Heading>
                <UnorderedList pl={3}>
                  {TOS_BULLETS.map((item, i) => (
                    <ListItem key={i} py={3} fontSize="sm">
                      {item}
                    </ListItem>
                  ))}
                </UnorderedList>
              </VStack>
              {/* Map data policy */}
              {DATA_POLICY.map((item, i) => (
                <VStack key={i} spacing={5} align="flex-start">
                  <Heading size="md">{item.heading}</Heading>
                  <Text fontSize="sm">{item.desc}</Text>
                </VStack>
              ))}
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </>
  );
};

export default TermsOfService;
