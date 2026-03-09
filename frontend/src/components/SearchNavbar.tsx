import { Field } from "./ui/field";
import { Input } from "./ui/input";

export default function SearchNavbar() {
  return (
    <div className="relative w-full max-w-full sm:w-96">
      <div className="relative">
        <Field>
          <Input
            placeholder="Search using a URL"
            className="bg-input/30 h-8 w-full rounded-sm shadow-none"
          />
        </Field>
      </div>
    </div>
  );
}
