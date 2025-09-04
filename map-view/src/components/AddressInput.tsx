import React, { useState } from 'react';
import {
  TextField,
  InputAdornment,
  Container,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import styles from './AddressInput.module.css';
import { Address } from '../common/AddressSearchUtils';

interface AddressInputProps {
  onSearch: (address: string) => void;
  onSelect: (result: Address) => void;
  results: Address[];
}

function AddressInput({ onSearch, onSelect, results }: AddressInputProps) {
  const [address, setAddress] = useState<string>('');

const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setAddress(value);
    // Only call onSearch if the length of the input value is 3 or more
    if (value.length >= 3) {
      onSearch(value);
    }
  };

  return (
    <Container className={styles.addressInputContainer}>
      <Box className="space-y-4">
          <Typography variant="h6" className="font-semibold text-gray-800">
          Enter Your Address
          </Typography>
          <TextField
          id="address-input"
          label="Full Address"
          variant="outlined"
          fullWidth
          value={address}
          onChange={handleChange}
          placeholder="e.g. Vaasankatu 20"
          startAdornment={
              <InputAdornment position="start">
              <HomeIcon className="text-gray-400" />
              </InputAdornment>
          }
          className="rounded-lg"
          />
          {results.length > 0 && (
          <List dense>
              {results.map((result, index) => (
              <ListItem key={index} button onClick={() => onSelect(result)}>
                  <ListItemText primary={result.name.fi} />
              </ListItem>
              ))}
          </List>
          )}
      </Box>
    </Container>
  );
}

export default AddressInput;