### PDF Catalog Generation App

The PDF Catalog Generation App is a robust and user-friendly tool designed for creating visually appealing and organized product catalogs in PDF format. This app is particularly useful for businesses and marketers who need to present their product offerings in a professional manner. Here's a detailed description of its features and functionality:

#### Key Features:

1. **Dynamic Data Export:**
   - The app connects to a Zoho Analytics workspace to fetch the latest product data.
   - It exports data from a specified view in CSV format, ensuring that the catalog contains the most up-to-date information.

2. **Subcategory Filtering:**
   - Users can filter products by subcategory, allowing for focused catalogs that highlight specific product lines or categories.
   - An option to include all subcategories is also available for comprehensive catalogs.

3. **Price Range Filtering:**
   - The app allows users to specify a price range, filtering products to display only those within the selected range.
   - This feature helps in targeting different market segments and catering to specific budget requirements.

4. **Image Handling:**
   - Product images are downloaded and resized to fit within the catalog layout, maintaining high quality while ensuring consistent presentation.
   - The app includes error handling to manage issues with image downloading gracefully.

5. **PDF Layout Customization:**
   - Users can choose between portrait and landscape orientations for the PDF.
   - The app dynamically adjusts the layout to accommodate various page sizes, margins, and image dimensions.
   - Each page can display multiple products, organized in a grid format for easy viewing.

6. **Interactive Elements:**
   - Product images in the PDF are hyperlinked, allowing viewers to click on an image to be redirected to the product's detailed page or purchase link.
   - This enhances the functionality of the catalog, making it not just a static document but an interactive marketing tool.

7. **Branding:**
   - The app incorporates branding elements such as logos and customized header text.
   - This ensures that the catalog aligns with the company’s branding guidelines and presents a professional image.

8. **Automatic Pagination:**
   - The app handles large volumes of data by automatically paginating the catalog.
   - It ensures that the content is evenly distributed across pages, providing a clean and organized look.

9. **Exception Handling and User Feedback:**
   - Comprehensive error handling ensures that any issues encountered during data fetching, image downloading, or PDF creation are managed smoothly.
   - Users are informed of the status and any errors through messages, improving the overall user experience.

#### Workflow:

1. **Data Fetching:**
   - The app fetches data from Zoho Analytics using the provided client credentials and workspace details.

2. **Data Filtering:**
   - Based on user input for subcategory and price range, the data is filtered to match the specified criteria.

3. **PDF Creation:**
   - The filtered data is used to create a PDF catalog.
   - The catalog includes product images, names, prices, and hyperlinks to product pages.

4. **PDF Output:**
   - The final PDF is saved and made available for download or distribution.

#### Use Cases:

- **Marketing Campaigns:**
  - Create catalogs for specific promotions or sales events.
- **Product Presentations:**
  - Generate professional product catalogs for presentations and meetings.
- **Customer Distribution:**
  - Provide customers with an easy-to-navigate catalog for online or offline browsing.

This app leverages Python libraries such as `pandas` for data manipulation, `requests` for handling HTTP requests, `PIL` for image processing, and `reportlab` for PDF generation, ensuring a seamless and efficient catalog creation process.
