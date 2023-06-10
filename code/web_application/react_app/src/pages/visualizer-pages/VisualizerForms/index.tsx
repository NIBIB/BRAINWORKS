import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Button,
  Container,
  Heading,
  HStack,
  IconButton,
  Text,
  Tooltip,
  useDisclosure,
  VStack,
} from "@chakra-ui/react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { FiInfo } from "react-icons/fi";

import FlaskForm from "../../../common/components/FlaskForm";
import usePageTitle from "../../../common/hooks/usePageTitle";
import useAPIDataAlert from "../../../common/hooks/useAPIDataAlert";
import PageHeader from "../../../common/components/PageHeader";
import VisualizerInfoModal from "../components/VisualizerInfoModal";
import FlaskField from "common/components/FlaskField";
import { VISUALIZER_FORMS } from "../templates";

/**
 * ToolForms
 *
 * Generates specific tool form based on given form key from URL, `form/:formkey`
 */
const ToolForms = () => {
  const params = useParams();
  const navigate = useNavigate();
  const { apiDataAlerter } = useAPIDataAlert();
  const { onOpen, isOpen, onClose } = useDisclosure();

  usePageTitle(`Visualizer form`);

  // * If cannot find tool in given URL, navigate back to the start
  if (!params.key || VISUALIZER_FORMS[params.key] === undefined) {
    return <Navigate to="/error404" />;
  }

  // * Constant to get all information from `VISUALIZER_FORMS` dictionary given form key
  const toolForm = VISUALIZER_FORMS[params.key];

  // * Handles on form submit
  const handleSubmit = (data: any, values: any) => {
    // * Successfully has all required forms filled in, send to tool page to build query
    const submitSuccess = () => {
      navigate("/visualizers/app");
    };
    // * Otherwise, alert success or give errors
    apiDataAlerter({
      data: data,
      onSuccess: () => {
        submitSuccess();
      },
      failureMsg: data.error,
    });
  };

  return (
    <>
      <VisualizerInfoModal
        representation={params.key}
        isOpen={isOpen}
        onClose={onClose}
      />
      <FlaskForm
        formKey={toolForm.formKey}
        runAfterSubmit={handleSubmit}
        noValidate={true}
        formSession={true}
      >
        {({ isSubmitting }) => (
          <Container maxW="4xl" my={100}>
            {/* Top heading */}
            <PageHeader
              subTitle="Customize"
              title="Design your visual"
              desc="Use over 40 years of scientific data to customize your visual."
              stackProps={{ mb: 100 }}
            />
            {/* Form card */}
            <Box
              bg="white"
              p={50}
              borderRadius="lg"
              boxShadow="sm"
              border="1px"
              borderColor="gray.200"
            >
              <HStack w="100%" justify="space-between" pb={50}>
                <HStack spacing={1}>
                  <Heading size="md">{toolForm.title}</Heading>
                  <Tooltip
                    color="white"
                    hasArrow
                    label={`Click to view information about ${toolForm.title}`}
                    aria-label="Tooltip to inform user that clicking this will open for more information"
                  >
                    <IconButton
                      variant="ghost"
                      size="sm"
                      color="gray.500"
                      aria-label={`See ${toolForm.title} information`}
                      icon={<FiInfo />}
                      onClick={onOpen}
                    />
                  </Tooltip>
                </HStack>
                {/* Submit */}
                <HStack>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      navigate("/visualizers");
                    }}
                  >
                    Return
                  </Button>
                  <Button
                    size="sm"
                    type="submit"
                    colorScheme="blue"
                    isDisabled={isSubmitting}
                  >
                    Submit
                  </Button>
                </HStack>
              </HStack>
              <VStack w="100%" spacing={5}>
                {/* Required fields */}
                {toolForm.required.map((field: any, index: number) => (
                  <FlaskField property={field.property} key={field.property} />
                ))}
                {/* Option fields if any exist */}
                {toolForm.optional.length > 0 && (
                  <Accordion allowToggle w="100%">
                    <AccordionItem>
                      <h2>
                        <AccordionButton color="gray.600">
                          <Box flex="1" textAlign="left">
                            Advanced {" "}
                            <Text
                              ml={2}
                              as="em"
                              display="inline"
                              fontStyle="italics"
                              fontSize="xs"
                            >
                              Optional
                            </Text>
                          </Box>
                          <AccordionIcon />
                        </AccordionButton>
                      </h2>
                      <AccordionPanel pb={4} minH="500px">
                        <VStack w="100%" spacing={5}>
                          {toolForm.optional.map(
                            (field: any, index: number) => (
                              <FlaskField
                                property={field.property}
                                key={field.property}
                              />
                            )
                          )}
                        </VStack>
                      </AccordionPanel>
                    </AccordionItem>
                  </Accordion>
                )}
              </VStack>
            </Box>
          </Container>
        )}
      </FlaskForm>
    </>
  );
};

export default ToolForms;
