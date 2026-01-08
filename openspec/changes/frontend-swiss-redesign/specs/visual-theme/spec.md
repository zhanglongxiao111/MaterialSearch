# Visual Theme Specification

## ADDED Requirements

### Requirement: Swiss International Style Theme
The workspace frontend MUST provide a Swiss International Style visual theme with the following characteristics.

#### Scenario: Color Scheme
**Given** the workspace is loaded
**When** viewing any page
**Then** the color palette MUST use:
- Primary background: light gray (#F4F4F4)
- Primary text: near-black (#111111)
- Sidebar background: deep black (#111111)
- Accent color: international orange (#FF3300)
- Muted text: gray (#888888)

#### Scenario: Typography
**Given** the workspace is loaded
**When** viewing UI elements
**Then** fonts MUST be applied as:
- UI text uses Inter font family
- Technical labels use JetBrains Mono font family
- Labels use UPPERCASE with letter-spacing 0.15em

#### Scenario: Border Radius
**Given** any UI component
**When** rendered on screen
**Then** all elements MUST have border-radius of 0px (sharp corners)

#### Scenario: Brand Identity
**Given** the workspace is loaded
**When** viewing the sidebar header
**Then** it displays "SA ARCHITECTS" as brand name
**And** displays "ASSET MANAGEMENT SYS." as subtitle

### Requirement: Responsive Sidebar
The sidebar MUST adapt to narrow screen widths.

#### Scenario: Default Sidebar Width
**Given** screen width >= 1024px
**When** viewing the workspace
**Then** the sidebar width is 320px

#### Scenario: Collapsible Sidebar on Narrow Screens
**Given** screen width < 768px
**When** viewing the workspace
**Then** the sidebar is hidden by default
**And** a hamburger menu button is visible
**When** the hamburger button is clicked
**Then** the sidebar slides in from the left

### Requirement: Feature Preservation
All existing workspace features MUST remain functional.

#### Scenario: Search Functionality
**Given** the Swiss theme is applied
**When** performing text search
**Then** search results display correctly
**And** waterfall/grid view toggle works
**And** single-image width adjustment works

#### Scenario: Upload Functionality
**Given** the Swiss theme is applied
**When** performing batch upload
**Then** all upload steps function correctly
**And** progress display works
**And** success/error reporting works
