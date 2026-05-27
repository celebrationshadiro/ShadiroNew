import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        // Primary: Deep blue - main CTA
        primary:
          "bg-primary text-primary-foreground shadow-md hover:bg-primary-dark hover:shadow-lg active:shadow-sm",
        
        // Secondary: Light gray - secondary actions
        secondary:
          "bg-secondary text-secondary-foreground border border-primary/20 hover:bg-primary/10 active:bg-primary/20",
        
        // Text/Ghost: Transparent - tertiary actions
        text: "text-primary hover:bg-primary/10 active:bg-primary/20",
        
        // Outline: Bordered - alternative actions
        outline:
          "border border-primary text-primary hover:bg-primary/5 active:bg-primary/10",
        
        // Premium: Gold accent - premium CTAs
        premium:
          "bg-accent text-accent-foreground shadow-md hover:bg-accent-dark hover:shadow-lg active:shadow-sm",
        
        // Danger: Red - destructive actions
        danger:
          "bg-error text-error-foreground shadow-sm hover:bg-error/90 active:shadow-none",
        
        // Ghost: Minimal - subtle interactions
        ghost: "hover:bg-muted active:bg-muted/80",
        
        // Link: Text-only
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        xs: "h-8 px-3 py-1 text-tiny",
        sm: "h-9 px-4 py-2 text-body-sm",
        default: "h-11 px-6 py-2.5 text-body-md",
        lg: "h-12 px-8 py-3 text-body-lg",
        xl: "h-14 px-10 py-3 text-body-lg",
        icon: "h-10 w-10",
        "icon-sm": "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  }
)

const Button = React.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button"
  return (
    <Comp
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      {...props} />
  );
})
Button.displayName = "Button"

export { Button, buttonVariants }
