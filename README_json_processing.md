# Chrono24 Data Analysis Module

This module provides comprehensive analysis capabilities for Chrono24 watch listings data stored in JSON format.

## Features

The `json_processing.py` module offers:

- **Price Statistics**: Average, median, standard deviation, min/max, variance
- **Shipping Cost Analysis**: Complete shipping price statistics
- **Total Cost Analysis**: Combined price + shipping statistics
- **Location Breakdown**: Statistics grouped by listing location
- **Merchant Analysis**: Compare dealers vs private sellers
- **Comprehensive Reporting**: All statistics in one summary

## Quick Start

### Method 1: Using Convenience Functions

```python
from json_processing import get_price_summary, get_shipping_summary, get_total_price_summary

# Quick price analysis
price_stats = get_price_summary("json_results/all_listings.json")
print(f"Average price: ${price_stats['average']:,.2f}")
print(f"Price std dev: ${price_stats['std_dev']:,.2f}")

# Quick shipping analysis
shipping_stats = get_shipping_summary("json_results/all_listings.json")
print(f"Average shipping: ${shipping_stats['average']:,.2f}")

# Quick total cost analysis
total_stats = get_total_price_summary("json_results/all_listings.json")
print(f"Average total cost: ${total_stats['average']:,.2f}")
```

### Method 2: Using the Analyzer Class

```python
from json_processing import Chrono24Analyzer

# Initialize analyzer
analyzer = Chrono24Analyzer("json_results/all_listings.json")

# Get comprehensive statistics
price_stats = analyzer.get_price_statistics()
shipping_stats = analyzer.get_shipping_statistics()
total_stats = analyzer.get_total_price_statistics()
location_stats = analyzer.get_location_statistics()
merchant_stats = analyzer.get_merchant_statistics()

# Get everything in one report
full_report = analyzer.get_summary_report()
```

## Available Statistics

### Price Statistics

- `count`: Number of valid price entries
- `average`: Mean price
- `median`: Median price
- `std_dev`: Standard deviation
- `min`: Minimum price
- `max`: Maximum price
- `variance`: Price variance

### Shipping Statistics

- Same metrics as price statistics, applied to shipping costs

### Total Price Statistics

- Same metrics applied to (price + shipping) totals

### Location Statistics

```python
location_stats = analyzer.get_location_statistics()
# Returns: {
#   "Location Name": {
#     "count": number_of_listings,
#     "avg_price": average_price,
#     "avg_shipping": average_shipping,
#     "price_std_dev": price_standard_deviation,
#     "shipping_std_dev": shipping_standard_deviation
#   }
# }
```

### Merchant Statistics

```python
merchant_stats = analyzer.get_merchant_statistics()
# Returns similar structure as location stats, grouped by merchant type
```

## Example Output

Based on the sample dataset:

```
=== PRICE STATISTICS ===
  count: 218 watches
  average: $15,403.67
  median: $14,998.00
  std_dev: $5,198.08
  range: $5,192.00 - $71,246.00

=== SHIPPING STATISTICS ===
  average: $141.35
  std_dev: $72.46
  range: $0.00 - $199.00

=== KEY INSIGHTS ===
• 86.2% from dealers, 13.8% from private sellers
• Dealers charge average $163.91 shipping
• Private sellers charge $0.00 shipping
• Price coefficient of variation: 33.7% (high diversity)
• Shipping adds 0.9% to total cost on average
```

## Data Format Requirements

The module expects JSON data with the following structure:

```json
[
  {
    "id": "listing_id",
    "price": "$10,023", // String with currency symbol and commas
    "shipping_price": "$199", // String format or "0"
    "location": "Antwerp, Belgium.",
    "merchant_name": "Dealer" // or "Private Seller"
    // ... other fields
  }
]
```

## Error Handling

- Handles missing or invalid price data gracefully
- Supports various currency symbols ($, €, £)
- Manages null/empty shipping prices (treats as $0)
- Returns error messages for empty datasets

## Usage Examples

See `example_usage.py` for a complete demonstration of all features.

Run the example:

```bash
python example_usage.py
```

## Requirements

- Python 3.7+
- Standard library only (no external dependencies)
