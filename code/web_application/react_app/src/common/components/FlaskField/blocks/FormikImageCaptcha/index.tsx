import DOMPurify from "dompurify";
import {
  Box,
  Divider,
  FormControl,
  Heading,
  HStack,
  IconButton,
  Image,
  Input,
  Skeleton,
  VStack,
} from "@chakra-ui/react";
import useGlobalFormik from "../../../../hooks/useGlobalFormik";
import Card from "../../../Card";
import { brandColorScheme } from "../../../../../setup/theme/colors";
import { FiRepeat } from "react-icons/fi";
import { Field, useFormikContext } from "formik";
import FormikValidationWrapper from "../FormikValidationWrapper";

/**
 * ImageCAPTCHA
 *
 * React component that renders an ImageCAPTCHA component that takes the `math` property
 */
const ImageCAPTCHA = () => {
  const { formikSlice, newCaptcha } = useGlobalFormik();
  const { captcha } = formikSlice;
  const formik = useFormikContext<any>();

  const field = formikSlice.fieldsInfo.filter(
    (item: any) => item.property === "math"
  )[0];

  return (
    <>
      <Card
        boxProps={{
          w: "auto",
          h: "auto",
          bg: "gray.50",
          p: 3,
        }}
      >
        <VStack spacing={2}>
          <Box w="100%">
            <Heading
              textAlign="left"
              fontSize="xs"
              color="gray.500"
              fontWeight={500}
              mb={2}
            >
              CAPTCHA
            </Heading>
            <Divider />
          </Box>
          <Skeleton
            startColor="white"
            endColor="white"
            isLoaded={captcha.img.length > 0}
            w="100%"
          >
            <Image
              border="1px"
              borderColor="gray.300"
              p={2}
              h={10}
              bg="white"
              w={"100%"}
              src={DOMPurify.sanitize(captcha.img)}
            />
          </Skeleton>
          <HStack align="flex-end" w="100%">
            <Box w="100%">
              <FormikValidationWrapper property="math">
                <Field
                  as={Input}
                  id="math"
                  autoComplete="off"
                  name="math"
                  noValidate={false}
                ></Field>
              </FormikValidationWrapper>
            </Box>
            {/* <IconButton
              colorScheme={brandColorScheme}
              aria-label="Volume"
              size="md"
              icon={<VolumeUp />}
              onClick={() => {
                const audio = new Audio(URL + captcha.audio);
                audio?.play();
              }}
            /> */}
            <IconButton
              colorScheme={brandColorScheme}
              aria-label="Refresh"
              size="md"
              icon={<FiRepeat />}
              onClick={newCaptcha}
            />
          </HStack>
        </VStack>
      </Card>
    </>
  );
};

export default ImageCAPTCHA;
