# Church Logo Setup Instructions

## How to Add Your Church Logo

The PHM-ARCC Church Management System is now configured to use your church logo throughout the application.

### Current Setup
- **Logo path**: `/media/church-logo.svg` (SVG format)
- **Used in**: Navigation bar, all dashboard sidebars, and player interfaces
- **Fallback**: Text-based "PHM-ARCC" branding if logo fails to load

### Adding Your Logo

1. **Replace the placeholder logo:**
   - Place your church logo at: `G:\project\church_system\church_management\media\church-logo.svg`
   - Recommended size: 32px height, proportional width
   - Format: SVG preferred, PNG also supported
   - The system will automatically resize and style it

2. **Supported formats:**
   - **SVG (Recommended)**: Scalable, small file size, crisp at any size
   - PNG: Good for complex images
   - JPG: For photographic logos
   - WebP: Modern format with good compression

3. **Logo styling:**
   - Automatically resized to 32px height
   - Rounded corners (4px border-radius)
   - Responsive design with fallback text

### Where Logo Appears

- **Navigation Bar**: Top left of all pages
- **Player Dashboard**: Sidebar header
- **Member Dashboard**: Sidebar header
- **Pastor Dashboard**: Sidebar header
- **Media Player**: Sidebar header
- **My Content**: Sidebar header

### Logo Requirements

- **Size**: Any size (will be resized to 32px height)
- **Format**: SVG, PNG, JPG, or WebP
- **Background**: Transparent recommended for best results
- **Content**: Church logo or emblem

### Testing

After adding your logo:
1. Restart the Django development server
2. Navigate to any page in the system
3. Your logo should appear in the navigation and sidebars
4. If logo doesn't load, the text fallback "PHM-ARCC" will appear

### Troubleshooting

**Logo not appearing:**
- ✅ Check file path: `media/church-logo.svg`
- ✅ Verify file permissions
- ✅ Restart the server
- ✅ Check browser developer tools for 404 errors

**Logo looks distorted:**
- Ensure original logo has good resolution
- Consider using SVG for best quality
- Logo will be resized to 32px height automatically

**Current Status:**
- ✅ Working SVG logo created
- ✅ All templates updated to use SVG
- ✅ Server running successfully
- ✅ Logo should now be visible

### Current Fallback Text

If logo fails to load, the system displays:
- **Church Name**: PHM-ARCC
- **Location**: Iyumbu Dodoma

This maintains professional branding even without a custom logo.

### Quick Fix Applied

I've created a working SVG logo and updated all templates. The logo should now be visible throughout the system. If you want to use your own logo:

1. Replace `media/church-logo.svg` with your logo file
2. Keep the same filename or update all templates to match your filename
3. Restart the server to see changes
